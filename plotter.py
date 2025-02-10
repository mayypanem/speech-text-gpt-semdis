import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import textwrap

# Looks better
plt.style.use('ggplot')


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
    if ratings_line==[]:
        # Dynamic plotting
        plt.ion()
        # Size 14x7 inches
        fig = plt.figure(figsize=(13,6))
        # No subplots
        ax = fig.add_subplot(111)
        # Set initial ylim range
        plt.ylim([0, 0.2])
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
            wrapped_text = "\n".join(textwrap.wrap(idea_annotations[i], width=15))
            ratings_line.axes.annotate(
                wrapped_text, # 2 decimal places
                (x_vec[i],y_data[i]), # Position (x,y)
                textcoords="offset points",
                xytext=(0,10), # Offset towards right
                ha='center', # Align text to left
                fontsize=10,
                color='black'
            )

    # Display ideas as text in the figure

    text_str = r"$\bf{EXTRACTED}$" + " " + r"$\bf{IDEAS}$" + "\n\n"
    for i in range(len(ideas_list)):
        formatted_rating = f"{ratings_list[i]:.2f}" if i < len(ratings_list) else ""
        text_str += ideas_list[i] + " " + rf"$\bf{{{formatted_rating}}}$" + "\n"

    plt.subplots_adjust(right=0.75)

    ratings_line.axes.text(
        1.05, 1.0, text_str,  # Move text slightly further right
        transform=ratings_line.axes.transAxes,
        fontsize=10, 
        horizontalalignment='left',  # Align left so text grows downward
        verticalalignment='top',  # Start at the top
        bbox=dict(boxstyle="round,pad=0.5", edgecolor='black', facecolor='white')  # Increase padding
    )

    # Adjust boundaries if a rating is outside the range 
    if np.max(y_data)>=ratings_line.axes.get_ylim()[1]:
        # Spacing to highest/lowest value: one standard deviation
        plt.ylim([0, np.max(y_data)+np.std(y_data)])
    # Update plot every t_pause seconds
    plt.pause(t_pause)

    # Return 
    return ratings_line