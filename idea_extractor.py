import warnings
warnings.simplefilter("ignore", UserWarning)

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
import google.api_core.exceptions
from plotter import live_plotter
import shutil
from datetime import datetime

### Task
TASK_ITEM = "brick"
TASK_DESCRIPTION = f"Come up with as many alternative uses as possible for a {TASK_ITEM}. Your goal is to be as creative as possible."

### Filenames
OPENAI_API_KEY_FILE = "OpenAI-API-key.txt"
GOOGLE_CLOUD_SPEECH_CREDENTIAL_FILE = "spech-text-gpt-semdis-f8647f2e5b71.json"
IDEA_PAIRS_FILENAME = "idea_pairs.csv"
RATINGS_FILENAME = "ratings.csv"
TRANSCRIPTS_FILENAME = "transcripts.csv"

### Variables
# Flag to stop the program
terminate_program = False
visualization_size = 20

### Google Cloud Speech
# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
# Load credentials
credentials = service_account.Credentials.from_service_account_file(GOOGLE_CLOUD_SPEECH_CREDENTIAL_FILE)

### OpenAI API
# Load API key
if not os.path.exists(OPENAI_API_KEY_FILE):
    raise FileNotFoundError(f"The file '{OPENAI_API_KEY_FILE}' was not found. Please create it and add your OpenAI API key.")
with open(OPENAI_API_KEY_FILE, "r") as file:
    openai_api_key = file.read().strip()
# Configure OpenAI API
client = OpenAI(api_key=openai_api_key)



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
            input_device_index=3,  # Change this index for different microphone
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

def save_ideas_to_csv(ideas_list, filename=IDEA_PAIRS_FILENAME):
    """Saves unique ideas to a CSV file and runs a SemDis API call."""
    
    if not ideas_list:
        print("No ideas to save!")
        return
    
    # Remove potential duplicates before saving
    unique_ideas = list(dict.fromkeys(ideas_list))

    #Save item-idea pairs to CSV
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(["item", "response"])
        # Write item-idea pairs
        for idea in unique_ideas:
            writer.writerow([TASK_ITEM, idea])

    print(f"Ideas saved to {filename}!")

    # Run semdis_api.py
    try:
        print("\nRunning semdis_api.py...")
        subprocess.run(["python", "semdis_api.py"], check=True)
        print("\nsemdis_api.py executed successfully!\n")
        # update_visualization()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running script: {e}")

def fill_list(ratings, target_length=20):
    if len(ratings) < target_length:
        # Prepend zeros if the list is too short
        return ratings + [0] * (target_length - len(ratings))
    else:
        # Keep only the last 20 elements if the list is too long
        return ratings[-target_length:]
    
def update_visualization(ideas_list):
    line = []
    size = visualization_size
    x_vec = np.linspace(0,1,size+1)[0:-1]
    while True:
        try:
            ideas, ratings = read_csv()

            # Ensure lists match in size
            ratings_filled = fill_list(ratings, size)
            ideas_filled = fill_list(ideas, size)
            
            # Call live_plotter with proper arguments
            line = live_plotter(x_vec, ratings_filled, line, ideas_list, ratings, idea_annotations=ideas_filled, title=TASK_DESCRIPTION)
        except Exception as e:
            print(f"Unexpected error: {e}")
        time.sleep(0.5)


def send_to_chatgpt(ideas_list, transcripts_list):
    # Process full transcript
    # TODO: explore transcript windows as an alternative and benchmark them
    latest_transcript = ' '.join(transcripts_list)

    if not latest_transcript.strip():
        print("Empty transcript!")
        return

    prompt = (
        f"Extract alternative uses for a {TASK_ITEM} from the following text:\n"
        f"{latest_transcript}\n\n"
        "Instructions:\n"
        "1. Extract only the alternative uses explicitly mentioned in the text. Do NOT, under any circumstances, add any ideas of your own.\n"
        "2. The extracted ideas must be **realistic and physically feasible**.\n"
        f"   - **Reject ideas that do not involve an actual function of a {TASK_ITEM}.**\n" # function -> use, affordance, "something you can do with x"
        "   - **Reject phrases that are just expressions, insults, or abstract concepts (e.g., 'be a dick').**\n"
        "   - Example: 'use as a nail' ❌ (bricks do not function as nails).\n" # mpre generic
        "   - Example: 'turn into a trampoline' ❌ (bricks do not bounce).\n"# kkkkkkkk
        "3. Compare with previous ideas:\n"
        f"{', '.join(ideas_list)}\n"
        "   - Do NOT return similar ideas (e.g., 'build a house' ≈ 'build a building').\n"
        "4. If no valid new ideas exist, return: New Ideas: none\n"
        "5. Format response as:\n"
        "New Ideas: idea1, idea2, idea3\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are an assistant that strictly extracts new ideas from transcripts. "
                                                    "You do NOT generate ideas, only extract them from user speech."},
                      {"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )

        answer = response.choices[0].message.content.strip()
        print(f"API Response: {answer}\n")

        # Extract ideas into list
        answer_ideas_string = re.search(r"New Ideas:\s*(.*)", answer, re.IGNORECASE)
        answer_ideas = answer_ideas_string.group(1).strip() if answer_ideas_string else ""
        if answer_ideas.lower() == "none":
            return []
        extracted_ideas = [idea.strip() for idea in answer_ideas.split(",")]

        # **Stronger Filtering:** Remove ideas that are exact OR similar duplicates
        new_ideas_filtered = [idea for idea in extracted_ideas if not is_similar(idea, ideas_list)]

        # No new ideas
        if not new_ideas_filtered:
            print("No truly new ideas detected after filtering.")
            return
        
        # Process new ideas
        print(f"New ideas: {new_ideas_filtered}")
        ideas_list.extend(new_ideas_filtered)
        print(f"Ideas List: {ideas_list}")
        save_ideas_to_csv(ideas_list)
        return
    
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return

def listen_print_loop(responses, ideas_list, transcripts_list):
    """Listens for speech and processes it in real time."""

    #Google Cloud Speech
    for response in responses:
        # Stop if ESC key was pressed
        if terminate_program:
            print("Terminating speech processing loop.\n")
            return
                
        if not response.results:
            continue
        result = response.results[0]
        if not result.alternatives:
            continue
        transcript = result.alternatives[0].transcript.strip()

        if result.is_final:
            # Ignore empty transcript
            if not transcript:
                continue
            # Process transcript content
            print(f"Transcript: {transcript}")
            # Add to list of transcripts
            transcripts_list.append(transcript)

            # Run OpenAI API request in separate thread
            processing_thread = threading.Thread(target=send_to_chatgpt, args=(ideas_list, transcripts_list), daemon=True)
            processing_thread.start()

def archive_session_data(transcripts_list):
    """Creates a timestamped folder, saves transcripts to a CSV, copies data files into it, moves it to 'data', and deletes the originals."""

    # Create a timestamped folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    folder_path = os.path.join(os.getcwd(), timestamp)
    os.makedirs(folder_path, exist_ok=True)

    # Create 'transcripts.csv' and save transcripts
    try:
        with open(TRANSCRIPTS_FILENAME, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for transcript in transcripts_list:
                writer.writerow([transcript])
        print(f"✅ Created {TRANSCRIPTS_FILENAME} with {len(transcripts_list)} transcripts.")
    except Exception as e:
        print(f"❌ Error creating {TRANSCRIPTS_FILENAME}: {e}")

    # List files to copy
    files_to_copy = [RATINGS_FILENAME, IDEA_PAIRS_FILENAME, TRANSCRIPTS_FILENAME]

    # Try copying files if they exist
    successfully_copied = []
    for file in files_to_copy:
        try:
            shutil.copy2(file, os.path.join(folder_path, file))
            print(f"✅ Copied {file} to {folder_path}")
            successfully_copied.append(file)  # Track successful copies
        except FileNotFoundError:
            print(f"⚠️ File {file} not found, skipping.")
        except Exception as e:
            print(f"❌ Error copying {file}: {e}")

    # Move the timestamped folder into the "data" folder
    data_folder = os.path.join(os.getcwd(), "data")
    os.makedirs(data_folder, exist_ok=True)
    try:
        final_destination = os.path.join(data_folder, timestamp)
        shutil.move(folder_path, final_destination)
        print(f"✅ Moved folder {folder_path} to {final_destination}")
    except Exception as e:
        print(f"❌ Error moving folder to 'data': {e}")
        # Prevent deletion if move fails
        return

    # Delete the original files after successful folder move
    for file in successfully_copied:
        try:
            os.remove(file)
            print(f"🗑️ Deleted original file: {file}")
        except Exception as e:
            print(f"❌ Error deleting {file}: {e}")

def escape_key_listener(microphone_stream, transcripts_list):
    """Waits for the ESC key press to terminate the program."""

    global terminate_program
    keyboard.wait("esc")  # Wait for ESC key press
    print("\nESC pressed. Stopping everything...\n")

    archive_session_data(transcripts_list)
    
    # Set flag to stop all loops
    terminate_program = True

    # Stop the microphone stream safely
    try:
        microphone_stream.closed = True
        if microphone_stream._audio_stream.is_active():
            microphone_stream._audio_stream.stop_stream()
        microphone_stream._audio_stream.close()
        microphone_stream._audio_interface.terminate()
    except Exception as e:
        print(f"Error closing microphone stream: {e}")

    # Exit the program forcefully if necessary
    sys.exit(0)


def main():
    print("\nStarting new idea extraction session...\n")

    # Reset files
    if os.path.exists(IDEA_PAIRS_FILENAME):
        os.remove(IDEA_PAIRS_FILENAME)
    with open(RATINGS_FILENAME, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(["item", "response"])
    print("Files reset successfully.")

    global terminate_program
    client = SpeechClient(credentials=credentials)
    ideas_list = []
    transcripts_list = []

    # Start visualization thread
    visualization_thread = threading.Thread(target=update_visualization, args=(ideas_list,), daemon=True)
    visualization_thread.start()
    print("Visualization started.")

    while not terminate_program:
        try:
            with MicrophoneStream(RATE, CHUNK) as stream:
                # Start escape key listener thread
                escape_thread = threading.Thread(target=escape_key_listener, args=(stream, transcripts_list), daemon=True)
                escape_thread.start()

                print("\n🎤 Now listening...\n")

                audio_generator = stream.generator()
                responses = client.streaming_recognize(
                    StreamingRecognitionConfig(config=RecognitionConfig(
                        encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                        sample_rate_hertz=RATE,
                        language_code="en-US",
                    ), interim_results=True), 
                    (StreamingRecognizeRequest(audio_content=content) for content in audio_generator)
                )

                listen_print_loop(responses, ideas_list, transcripts_list)

        except google.api_core.exceptions.OutOfRange as e:
            print(f"\nStream duration exceeded (5 min limit). Restarting...\nException: {e}")
            continue  # Restarts the loop safely

        except KeyboardInterrupt as e:
            print(f"Keyboard Interrupt: {e}")
            terminate_program = True
            break  # Exit loop safely

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    print("👋 Exiting program. Goodbye!")

if __name__ == "__main__":
    main()