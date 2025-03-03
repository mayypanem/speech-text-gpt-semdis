import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import textwrap

# Looks better
plt.style.use('ggplot')

ANNOTATION_OFFSET_UP = 10
ANNOTATION_OFFSET_DOWN = -25

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

def live_plotter(x_vec, y_data, ratings_line, ideas_list, ratings_list, idea_annotations=None, title="AUT for brick", t_pause=0.5):
    """
    Updates a live plot with new creativity ratings.

    Parameters:
    - x_vec (numpy.ndarray): Fixed x-axis values
    - y1_data (numpy.ndarray): Dynamic creativity ratings to be updated
    - ratings_line (matplotlib.lines.Line2D or list): Line object for updating the plot. Pass an empty list `[]` initially.
    - idea_annotations (list, optional): Custom text annotations for each point (default: None)
    - title (str, optional): Title of the plot (default: '')
    - t_pause (float, optional): Time (in seconds) to pause for UI updates (default: 0.1s)

    Returns:
    - line1 (matplotlib.lines.Line2D): Updated line object for further updates.
    """
    annotation_offsets = position_annotations(y_data) if y_data else []
    if ratings_line==[]:
        # Dynamic plotting
        plt.ion()
        # Size 14x7 inches
        fig = plt.figure(figsize=(13,6))
        # No subplots
        ax = fig.add_subplot(111)
        # Set initial ylim range
        plt.ylim([0, 0.3])
        # Hide x-axis labels
        ax.set_xticklabels([])
        # Create variable to reference later
        ratings_line, = ax.plot(x_vec,y_data,'-o')
        plt.ylabel('Creativity Rating')
        plt.title(title)
        # Add padding for annotations
        padding = 0.1 * (x_vec[-1] - x_vec[0])  # 10% of the x-range
        ax.set_xlim(x_vec[0] - padding, x_vec[-1] + padding)
        plt.draw()
    
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
                wrapped_text, # 2 decimal places
                (x_vec[i],y_data[i]), # Position (x,y)
                textcoords="offset points",
                xytext=(0,annotation_offsets[i]),
                ha='center',
                fontsize=9,
                fontweight='bold',
                color='black'
            )

    # Display ideas as text in the figure

    text_str = r"$\bf{EXTRACTED}$" + " " + r"$\bf{IDEAS}$" + "                    \n\n"
    for i in range(len(ideas_list)):
        idea = ideas_list[i]
        list_entry = ""
        if i < len(ratings_list):
            formatted_rating = f"{ratings_list[i]:.2f}"
            list_entry += rf"$\bf{{{formatted_rating}}}$" + " " + idea + "\n"
        else:
            # text_str += "$\mathit{" + idea.replace(" ", r"\ ") + "}$" + " ...\n"
            list_entry += r"$\mathit{(...)}$" + " " + idea + "\n"
        wrapped_list_entry = "\n".join(textwrap.wrap(list_entry, width=40)) + "\n"
        text_str += wrapped_list_entry


    plt.subplots_adjust(right=0.75)

    ratings_line.axes.text(
        1.05, 1.0, text_str,
        transform=ratings_line.axes.transAxes,
        fontsize=8, 
        horizontalalignment='left',  # Align left so text grows downward
        verticalalignment='top',  # Start at the top
        bbox=dict(boxstyle="round,pad=0.5", edgecolor='black', facecolor='white', linewidth=2)
    )

    # Adjust boundaries if a rating is outside the range 
    if np.max(y_data)+0.1>=ratings_line.axes.get_ylim()[1]:
        # Spacing to highest/lowest value: one standard deviation
        plt.ylim([0, np.max(y_data)+0.1])
    # Update plot every t_pause seconds
    plt.pause(t_pause)

    # Return 
    return ratings_line