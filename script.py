import pyaudio
import wave
import speech_recognition as sr
from openai import OpenAI
import pandas as pd
import os

# Load OpenAI API key from a text file
key_file = "OpenAI-API-key.txt"
openai_api_key = ""
if not os.path.exists(key_file):
    raise FileNotFoundError(f"The file '{key_file}' was not found. Please create it and add your OpenAI API key.")
with open(key_file, "r") as file:
    openai_api_key = file.read().strip()

# Configure OpenAI API
client = OpenAI(
  api_key=openai_api_key
)

# CSV setup
output_file = "chatgpt_responses.csv"

# Create or load the CSV
if not os.path.exists(output_file):
    df = pd.DataFrame(columns=["Input Text", "ChatGPT Response"])
    df.to_csv(output_file, index=False)
else:
    df = pd.read_csv(output_file)

def record_audio():
    """
    Records live audio and saves it to a temporary WAV file.
    """
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 30  # Adjust as needed
    WAVE_OUTPUT_FILENAME = "temp_audio.wav"

    p = pyaudio.PyAudio()

    print("Recording...")
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=3, #change index for different microphone
                    frames_per_buffer=CHUNK)

    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return WAVE_OUTPUT_FILENAME

def transcribe_audio(audio_file):
    """
    Transcribes audio using Google Speech-to-Text.
    """
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)

    try:
        print("Transcribing...")
        text = recognizer.recognize_google(audio)
        print(f"Transcription: {text}")
        return text
    except sr.UnknownValueError:
        print("Google Speech-to-Text could not understand the audio.")
    except sr.RequestError as e:
        print(f"Google Speech-to-Text API error: {e}")

    return None

def send_to_chatgpt(prompt):
    """
    Sends transcribed text to ChatGPT and retrieves a response.
    """
    try:
        print("Sending to ChatGPT...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                "role": "system",
                "content": "You will be provided with a series of words. Your task is to add correct punctuation to form coherent sentences."
                },
                {
                "role": "user",
                "content": prompt
                }
            ],
            max_tokens=4096,  # Adjust the token limit as needed
            temperature=0.7  # Adjust creativity level (0.0 is deterministic, 1.0 is more random)
        )

        answer = response.choices[0].message.content
        print(f"ChatGPT Response: {answer}")
        return answer
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None

def find_audio_device_index():
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        print(p.get_device_info_by_index(i))
    p.terminate()

def main():
    # find_audio_device_index() necessary when trying to identify different microphone
    while True:
        # Step 1: Record audio
        audio_file = record_audio()

        # Step 2: Transcribe audio
        text = transcribe_audio(audio_file)

        if text:
            # Step 3: Send transcription to ChatGPT
            response = send_to_chatgpt(text)

            if response:
                # Step 4: Save the input and response to a CSV file
                global df
                new_row = pd.DataFrame({"Input Text": [text], "ChatGPT Response": [response]})
                df = pd.concat([df, new_row], ignore_index=True)  # Combine the existing and new row
                df.to_csv(output_file, index=False)  # Save to CSV

        # Prompt to continue or quit
        cont = input("Do you want to record another audio clip? (yes/no): ")
        if cont.strip().lower() != "yes":
            break

if __name__ == "__main__":
    main()
