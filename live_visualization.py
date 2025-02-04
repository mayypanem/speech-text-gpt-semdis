import csv
import time
import matplotlib.pyplot as plt
import numpy as np
import os

CSV_FILENAME = "processed_results.csv"
UPDATE_SIGNAL = "update_signal.txt"

# ✅ Create figure and axes once (not inside the update function)
plt.ion()  # Enable interactive mode
fig, ax = plt.subplots(figsize=(10, 2))  # Keep figure open

def read_csv():
    """Reads CSV and extracts responses and predictions."""
    try:
        with open(CSV_FILENAME, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            
            responses, predictions = [], []
            for row in reader:
                responses.append(row[1])  # Second column (response)
                predictions.append(float(row[2]))  # Third column (prediction)

            return responses, predictions
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return [], []

def update_visualization():
    """Updates the existing plot instead of creating a new one."""
    responses, predictions = read_csv()
    if not responses or not predictions:
        print("⚠️ No valid data to visualize.")
        return

    ax.clear()  # ✅ Clear only the plot, not the figure

    # ✅ Draw a persistent horizontal scale from 0 to 1
    ax.hlines(y=0, xmin=0, xmax=1, color="black", linewidth=2)  # Baseline

    # ✅ Scatter plot markers to show prediction values
    ax.scatter(predictions, [0] * len(predictions), color="red", s=100, zorder=3)  

    # ✅ Add labels above each point
    for x, label in zip(predictions, responses):
        ax.text(x, 0.1, label, ha="center", va="bottom", fontsize=10, fontweight="bold", rotation=45)

    # ✅ Maintain the same fixed scale
    ax.set_xlim(0, 1)  # Fixed scale from 0 to 1
    ax.set_ylim(-0.2, 0.5)  # Allow space for labels
    ax.set_xticks(np.linspace(0, 1, 11))  # Show ticks from 0 to 1
    ax.set_yticks([])  # Remove y-axis labels
    ax.set_xlabel("Prediction Score")
    ax.set_title("Real-Time Prediction Visualization")

    plt.draw()  # ✅ Update the existing figure
    plt.pause(0.1)  # ✅ Keep the window responsive

def watch_for_updates():
    """Continuously watches for updates and refreshes visualization."""
    update_visualization()  # Initial visualization

    while True:
        if os.path.exists(UPDATE_SIGNAL):  
            print("🔄 Update detected! Refreshing visualization in the same window...")

            time.sleep(0.5)  # ✅ Allow time for CSV writing before reading it

            if os.path.exists(UPDATE_SIGNAL):  # ✅ Double-check before removing
                update_visualization()
                os.remove(UPDATE_SIGNAL)  # ✅ Remove the update signal only once
            else:
                print("⚠️ Update signal file was already removed by another process.")

            plt.pause(1)  # ✅ Prevents excessive updates


if __name__ == "__main__":
    print("📡 Visualization started. Waiting for updates...")

    # ✅ Ensure the update signal file exists before starting
    if not os.path.exists(UPDATE_SIGNAL):
        open(UPDATE_SIGNAL, 'w').close()  # ✅ Create an empty update signal file

    watch_for_updates()
