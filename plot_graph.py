import matplotlib.pyplot as plt
import numpy as np
import textwrap
import csv
import time

RATINGS_FILENAME = "data/Marco/ratings.csv"
ANNOTATION_OFFSET_UP = 10
ANNOTATION_OFFSET_DOWN = -25
initial_xmin = 0
initial_xmax = 10

# Looks better
plt.style.use('ggplot')

def read_csv():
    """Reads CSV and extracts ideas and ratings."""
    try:
        with open(RATINGS_FILENAME, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            # Skip header
            next(reader)

            ideas, ratings = [], []
            for row in reader:
                ideas.append(row[1])  # Second column (idea)
                ratings.append(float(row[2]))  # Third column (rating)

            return ideas, ratings
    except Exception as e:
        global terminate_program
        if not terminate_program:
            print(f"Error reading CSV: {e}")
        return [], []

def position_annotations(y_data):
    # All annotations start with offset 0
    positions = [0] * len(y_data)
    if y_data:
        # Mark peaks and valleys
        positions[0] = peak_valley(y_data[0],y_data[0],y_data[1]) # first
        positions[len(y_data)-1] = peak_valley(y_data[len(y_data)-2],y_data[len(y_data)-1],y_data[len(y_data)-1]) # last
        for i in range(1, len(positions) - 1):
            positions[i] = peak_valley(y_data[i-1], y_data[i], y_data[i+1]) # others
        # Mark neighbors to peaks and valleys
        position_neighbors(positions, y_data)
    print(positions)
    return positions

def peak_valley (left,point,right):
    # peak -> annotation above
    if point >= left and point >= right:
        return ANNOTATION_OFFSET_UP
    # valley -> annotation below
    elif point <= left and point <= right:
        return ANNOTATION_OFFSET_DOWN
    else:
        return 0

def position_neighbors(positions, y_data):
    # Only position when both neighbors are positioned
    for i in range(1, len(positions) - 1):
        left = positions[i-1]
        right = positions[i+1]
        dif_left = abs(y_data[i-1]-y_data[i])
        dif_right = abs(y_data[i+1]-y_data[i])
        if positions[i] == 0: # not positioned yet
            if left != 0 and right != 0: # neighbors positioned
                if dif_left > dif_right: # left neighbor is further away
                    positions[i] = left # shift label in same direction as left neighbor
                else:
                    positions[i] = right
        else: # already positioned
            continue
    # Position the rest
    for i in range(1, len(positions) - 1):
        left = positions[i-1]
        right = positions[i+1]
        dif_left = abs(y_data[i-1]-y_data[i])
        dif_right = abs(y_data[i+1]-y_data[i])
        if positions[i] == 0: # not positioned yet
            if dif_left > dif_right: # left neighbor is further away
                positions[i] = ANNOTATION_OFFSET_UP if y_data[i-1]>y_data[i] else ANNOTATION_OFFSET_DOWN # shift annotation towards left neighbor
            else:
                positions[i] = ANNOTATION_OFFSET_UP if y_data[i+1]>y_data[i] else ANNOTATION_OFFSET_DOWN #shift annotation towards right neighbor
        else: # already positioned
            continue
    
def split_into_two_lines(text):
    """Splits a string into two lines of approximately equal length."""
    words = text.split()
    # If it's a single word, return as is
    if len(words) == 1:  
        return text
    
    first_line = [words[0]]
    second_line = [words[-1]]
    words = words[1:-1]

    while len(words) > 0:
        len_first_line = sum(len(word) for word in first_line) + len(first_line) - 1
        len_second_line = sum(len(word) for word in second_line) + len(second_line) - 1
        if len_first_line > len_second_line:
            second_line.insert(0,words.pop())
        else:
            first_line.append(words.pop(0))
    return " ".join(first_line) + "\n" + " ".join(second_line)

def live_plotter(y_data, ratings_line, ideas_list, idea_annotations=None, title="AUT for brick", t_pause=0.5):
    """
    Updates a live plot with new creativity ratings.

    Parameters:
    - y_data (numpy.ndarray): Creativity ratings to be updated
    - ratings_line (matplotlib.lines.Line2D or list): Line object for updating the plot. Pass an empty list `[]` initially.
    - ideas_list: extracted ideas before semdis API call
    - idea_annotations (list, optional): Custom text annotations for each point (default: None)
    - title (str, optional): Title of the plot (default: '')
    - t_pause (float, optional): Time (in seconds) to pause for UI updates (default: 0.1s)

    Returns:
    - line1 (matplotlib.lines.Line2D): Updated line object for further updates.
    """
    annotation_offsets = position_annotations(y_data)
    # Indices where annotations should be fixed
    fixed_indices = {i for i, val in enumerate(annotation_offsets) if val != 0}
    x_vec = x_vec = list(range(1, len(y_data)+1)) if y_data else []

    if ratings_line==[]:
        # Dynamic plotting
        plt.ion()
        # Size 14x7 inches
        fig = plt.figure(figsize=(14,6))
        # No subplots
        ax = fig.add_subplot(111)
        # Set initial xlim and ylim range
        plt.xlim([initial_xmin,initial_xmax])
        plt.ylim([0, 0.2])
        # Create variable to reference later
        ratings_line, = ax.plot(x_vec,y_data,'-o')
        plt.ylabel('Creativity Rating')
        plt.title(title)
        # Add padding for annotations
        ax.set_xlim(initial_xmin, initial_xmax + 0.99)
        plt.draw()

    #Adjust x boundaries if there are more ideas than the current boundaries allow for
    if ratings_line.axes.get_xlim()[1] < len(x_vec):
        plt.xlim([initial_xmin, len(x_vec) + 0.99])
    
    # Adjust y boundaries if a rating is outside the range 
    if np.max(y_data)>=ratings_line.axes.get_ylim()[1]:
        # Spacing to highest: one standard deviation
        plt.ylim([0, np.max(y_data)+np.std(y_data)])


    # Set idea ratings data
    ratings_line.set_ydata(y_data)

    #Clear previous annotations
    for txt in ratings_line.axes.texts:
        txt.remove()

    # Annotate each point
    for i in range(len(x_vec)):
        if idea_annotations[i] == 0:
            continue
        else:
            wrapped_text = split_into_two_lines(idea_annotations[i])
            ratings_line.axes.annotate(
                wrapped_text,
                (x_vec[i],y_data[i]),
                textcoords="offset points",
                xytext=(0,annotation_offsets[i]),
                ha='center',
                fontsize=9,
                fontweight='bold',
                color='black'
            )

    # Display ideas as text in the figure
    text_str = r"$\bf{EXTRACTED}$" + " " + r"$\bf{IDEAS}$" + "           \n\n"
    for i in range(len(ideas_list)):
        idea = ideas_list[i]
        list_entry = ""
        if i < len(y_data):
            formatted_rating = f"{y_data[i]:.2f}"
            list_entry += idea + " " + rf"$\bf{{{formatted_rating}}}$" + "\n"
        else:
            # text_str += "$\mathit{" + idea.replace(" ", r"\ ") + "}$" + " ...\n"
            list_entry += idea + " " + r"$\mathit{(...)}$" + "\n"
        wrapped_list_entry = "\n".join(textwrap.wrap(list_entry, width=40)) + "\n"
        text_str += wrapped_list_entry

    plt.subplots_adjust(right=0.75)

    ratings_line.axes.text(
        1.05, 1.0, text_str,
        transform=ratings_line.axes.transAxes,
        fontsize=9, 
        horizontalalignment='left',  # Align left so text grows downward
        verticalalignment='top',  # Start at the top
        bbox=dict(boxstyle="round,pad=0.5", edgecolor='black', facecolor='white', linewidth=2)
    )

    # Update plot every t_pause seconds
    plt.pause(t_pause)
    # Return 
    return ratings_line

def main():
    line = []
    
    while True:
        try:
            ideas, ratings = read_csv()
            ideas_list = ideas
            
            # Call live_plotter with proper arguments
            line = live_plotter(ratings, line, ideas_list, idea_annotations=ideas, title="test")
        except Exception as e:
            print(f"Unexpected error: {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    main()