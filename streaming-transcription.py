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

# Flag to stop the program when ESC is pressed
terminate_program = False

# Load OpenAI API key
key_file = "OpenAI-API-key.txt"
if not os.path.exists(key_file):
    raise FileNotFoundError(f"The file '{key_file}' was not found. Please create it and add your OpenAI API key.")
with open(key_file, "r") as file:
    openai_api_key = file.read().strip()

# Configure OpenAI API
client = OpenAI(api_key=openai_api_key)

# Load Google Cloud Speech credentials
credentials = service_account.Credentials.from_service_account_file(
    r"C:\Users\majas\Documents\GitHub\speech-text-gpt-semdis\spech-text-gpt-semdis-f8647f2e5b71.json"
)

class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            input_device_index=3,  # Change index for different microphone
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        """Yields audio chunks from the stream."""
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            yield chunk

def is_similar(new_idea, existing_ideas, similarity_threshold=0.8):
    """Checks if a new idea is similar to any in the existing ideas list using fuzzy matching."""
    close_matches = get_close_matches(new_idea, existing_ideas, n=1, cutoff=similarity_threshold)
    return len(close_matches) > 0

def start_visualization():
    """Starts the visualization in the main thread without freezing."""
    global fig, ax  # ✅ Use the same figure globally

    if fig is None or ax is None:  # ✅ Create only if it doesn’t exist
        print("📊 Starting visualization...")
        plt.ion()  # ✅ Enable interactive mode
        fig, ax = plt.subplots(figsize=(5, 8))  # ✅ Adjust window size for vertical layout
        plt.show(block=False)  # ✅ Prevents Matplotlib from freezing

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



def save_ideas_to_csv(ideas_list, filename=CSV_FILENAME):
    """Saves unique ideas to a CSV file and updates visualization."""
    if not ideas_list:
        print("⚠️ No ideas to save!")
        return

    unique_ideas = list(set(ideas_list))  # Remove duplicates before saving

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["item", "response"])  # Write header

        for idea in unique_ideas:
            writer.writerow(["brick", idea])

    print(f"✅ Ideas saved to {filename}!")

    # Run semdisAPI-script.py
    try:
        print("🔄 Running semdisAPI-script.py...")
        subprocess.run(["python", "semdisAPI-script.py"], check=True)
        print("✅ semdisAPI-script.py executed successfully!")

        # ✅ Ensure visualization updates immediately
        print("🔄 Updating visualization...")
        update_visualization()  # No plt.pause(1) here
        print("✅ Visualization updated!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error running script: {e}")


def send_to_chatgpt(ideas_list, transcripts_list):
    latest_transcript = ' '.join(transcripts_list)  # Keep full transcript history
    if not latest_transcript.strip():
        print("⚠️ Empty transcript - Not sending to ChatGPT.")
        return None

    prompt = (
        "Extract alternative uses for a brick from the following text:\n"
        f"{latest_transcript}\n\n"
        "Instructions:\n"
        "1. Extract only the alternative uses explicitly mentioned in the text. Do NOT, under any circumstances, add any ideas of your own.\n"
        "2. The extracted ideas must be **realistic and physically feasible**.\n"
        "   - **Reject ideas that do not involve an actual function of a brick.**\n"
        "   - **Reject phrases that are just expressions, insults, or abstract concepts (e.g., 'be a dick').**\n"
        "   - Example: 'use as a nail' ❌ (bricks do not function as nails).\n"
        "   - Example: 'turn into a trampoline' ❌ (bricks do not bounce).\n"
        "3. Compare with previous ideas:\n"
        f"{', '.join(ideas_list)}\n"
        "   - Do NOT return similar ideas (e.g., 'build a house' ≈ 'build a building').\n"
        "4. If no valid new ideas exist, return: New Ideas: none\n"
        "5. Format response as:\n"
        "New Ideas: idea1, idea2, idea3\n"
    )

    try:
        print("Sending to ChatGPT...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are an assistant that strictly extracts new ideas from transcripts. "
                                                    "You do NOT generate ideas, only extract them from user speech."},
                      {"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )

        answer = response.choices[0].message.content.strip()
        print(f"ChatGPT Response: {answer}")

        # Extract ideas using regex
        match = re.search(r"New Ideas:\s*(.*)", answer, re.IGNORECASE)
        new_ideas = match.group(1).strip() if match else ""

        if new_ideas.lower() == "none":
            return []

        # Split and filter new ideas
        extracted_ideas = [idea.strip() for idea in new_ideas.split(",")]

        # **Stronger Filtering:** Remove ideas that are exact OR similar duplicates
        new_ideas_filtered = [idea for idea in extracted_ideas if not is_similar(idea, ideas_list)]

        if not new_ideas_filtered:
            print("⚠️ No truly new ideas detected after filtering.")
            return []

        ideas_list.extend(new_ideas_filtered)
        save_ideas_to_csv(ideas_list)

        return new_ideas_filtered
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return []

def listen_print_loop(responses, ideas_list):
    """Listens for speech and processes it in real time."""
    transcripts_list = []  # Stores full history

    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript.strip()

        if result.is_final:
            if not transcript:
                continue  # Ignore empty speech

            print(f"Final Transcript: {transcript}")
            transcripts_list.append(transcript)  # No limit on history

            result = send_to_chatgpt(ideas_list, transcripts_list)
            print(f"Ideas List: {ideas_list}")

def escape_key_listener(microphone_stream):
    """Waits for the ESC key press to terminate the program."""
    global terminate_program
    keyboard.wait("esc")  # Wait until ESC is pressed
    print("\n🚨 Escape key pressed. Stopping everything...\n")
    
    # ✅ Stop the microphone stream safely
    terminate_program = True  # Signal the main loop to stop
    microphone_stream.closed = True
    microphone_stream._audio_stream.stop_stream()
    microphone_stream._audio_stream.close()
    microphone_stream._audio_interface.terminate()

def main():
    global terminate_program
    client = SpeechClient(credentials=credentials)
    ideas_list = []

    start_visualization()  # ✅ Start visualization in the main thread

    while not terminate_program:  # ✅ Keep running until ESC is pressed
        try:
            with MicrophoneStream(RATE, CHUNK) as stream:
                print("🎤 Starting new speech-to-text session (max duration: 5 minutes)...")

                audio_generator = stream.generator()
                responses = client.streaming_recognize(
                    StreamingRecognitionConfig(config=RecognitionConfig(
                        encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz=RATE,
                        language_code="en-US",
                    ), interim_results=True), 
                    (StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
                )

                listen_print_loop(responses, ideas_list)

                # ✅ Keep Matplotlib fully responsive in the main thread
                update_visualization()  
                fig.canvas.flush_events()  # ✅ Forces UI updates
                plt.pause(0.1)  # ✅ Allows smooth interactions

        except google.api_core.exceptions.OutOfRange as e:
            print(f"\n⚠️ Stream duration exceeded (5 min limit). Restarting...\nException: {e}")
            continue  # ✅ Restarts the loop safely

        except KeyboardInterrupt:
            print("\n🚨 Escape key pressed. Stopping everything...\n")
            terminate_program = True
            break  # ✅ Exit loop safely

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            break

    print("👋 Exiting program. Goodbye!")

if __name__ == "__main__":
    main()