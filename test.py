from google.cloud.speech import RecognitionConfig, StreamingRecognitionConfig, StreamingRecognizeRequest, SpeechClient
import pyaudio
from six.moves import queue
from google.oauth2 import service_account
from openai import OpenAI
import os
import re
import csv
import itertools
import keyboard  # Detect space key press
import threading  # Run space key listener separately
from difflib import get_close_matches
import sys
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import csv
import time
import google.api_core.exceptions  # ✅ Add this to fix NameError

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
CSV_FILENAME = "ideas_pairs.csv"



# Global variable for visualization process
visualization_process = None
CSV_RESULTS_FILENAME = "processed_results.csv"
# ✅ Create figure and axes once, not inside the update function
plt.ion()  # Interactive mode keeps the figure open
fig, ax = None, None

def start_visualization():
    """Starts the visualization in the main thread without freezing."""
    global fig, ax  # ✅ Use the same figure globally

    if fig is None or ax is None:  # ✅ Create only if it doesn’t exist
        print("📊 Starting visualization...")
        plt.ion()  # ✅ Enable interactive mode
        fig, ax = plt.subplots(figsize=(5, 8))  # ✅ Adjust window size for vertical layout
        plt.show(block=False)  # ✅ Prevents Matplotlib from freezing
    else:
        print("why not")

    update_visualization()  # ✅ First-time update so it's not empty
    plt.pause(0.01)  # ✅ Small pause to ensure Matplotlib processes GUI events

def read_csv():
    """Reads CSV and extracts responses and predictions."""
    try:
        with open(CSV_RESULTS_FILENAME, "r", encoding="utf-8") as file:
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
    """Updates the existing plot with a vertical orientation and prevents freezing."""
    global fig, ax

    # ✅ Ensure figure and axis exist before updating
    if fig is None or ax is None:
        print("📊 Initializing visualization window...")
        plt.ion()
        fig, ax = plt.subplots(figsize=(5, 8))
        plt.show(block=False)

    try:
        responses, predictions = read_csv()

        if not responses or not predictions:
            print("⚠️ No valid data to visualize.")
            return

        ax.clear()

        # ✅ Flip the graph: Use predictions on Y-axis instead of X-axis
        ax.scatter([0] * len(predictions), predictions, color="red", s=100, zorder=3)  

        # ✅ Adjust label positioning dynamically
        for y, label in zip(predictions, responses):
            ax.text(
                0.05, y,
                label,
                ha="left", va="center",
                fontsize=10, fontweight="bold",
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle="round,pad=0.3")
            )

        # ✅ Adjust axis limits for a vertical graph
        ax.set_ylim(0, 1)
        ax.set_xlim(-0.1, 0.3)
        ax.set_yticks(np.linspace(0, 1, 11))
        ax.set_xticks([])
        ax.set_ylabel("Prediction Score")
        ax.set_title("Real-Time Prediction Visualization (Vertical)", fontsize=12)

        plt.draw()
        fig.canvas.flush_events()  # ✅ Forces GUI to process events, prevents freezing
        plt.pause(0.01)  # ✅ Small delay to keep UI responsive

        print("✅ Visualization updated without freezing!")

    except Exception as e:
        print(f"❌ Error in update_visualization: {e}")

def main():
    start_visualization()
    update_visualization()
    time.sleep(5)

if __name__ == "__main__":
    main()