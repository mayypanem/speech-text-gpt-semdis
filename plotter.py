import matplotlib.pyplot as plt
import numpy as np

# Looks better
plt.style.use('ggplot')


def live_plotter(x_vec, y_data, ratings_line, title="AUT for brick", t_pause=0.1):
    """
    Updates a live plot with new creativity ratings.

    Parameters:
    - x_vec (numpy.ndarray): Fixed x-axis values
    - y1_data (numpy.ndarray): Dynamic creativity ratings to be updated
    - ratings_line (matplotlib.lines.Line2D or list): Line object for updating the plot. Pass an empty list `[]` initially.
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
        # Create variable to reference later
        ratings_line, = ax.plot(x_vec,y_data,'-o')
        plt.ylabel('Creativity Rating')
        plt.title(title)
        plt.show()
    
    # Set idea ratings data
    ratings_line.set_ydata(y_data)

    #Clear previous annotations
    for txt in ratings_line.axes.texts:
        txt.remove()
    # Annotate each point
    for i in range(len(x_vec)):
        ratings_line.axes.annotate(
            f'{y_data[i]:.2f}', # 2 decimal places
            (x_vec[i],y_data[i]), # Position (x,y)
            textcoords="offset points",
            xytext=(10,0), # Offset towards right
            ha='left', # Align text to left
            fontsize=8,
            color='black'
        )

    # Adjust boundaries if a rating is outside the range 
    if np.min(y_data)<=ratings_line.axes.get_ylim()[0] or np.max(y_data)>=ratings_line.axes.get_ylim()[1]:
        # Spacing to highest/lowest value: one standard deviation
        plt.ylim([np.min(y_data)-np.std(y_data), np.max(y_data)+np.std(y_data)])
    # Update plot every t_pause seconds
    plt.pause(t_pause)

    # Return 
    return ratings_line