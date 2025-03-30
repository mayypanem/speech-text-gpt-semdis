# 💡 Real-Time Idea Extraction and Novelty Visualization Tool

This Python-based tool enables **real-time extraction of creative ideas** from speech and visualizes their **semantic novelty** using the SemDis API. Originally developed for evaluating creativity in tasks like the **Alternative Uses Task (AUT)**, the system combines speech recognition, large language models (LLMs), semantic distance scoring, and live visualization into a modular research tool.

---

## ⚙️ Setup

### 1. Clone the Repository
```bash
git clone https://github.com/mayypanem/speech-text-gpt-semdis.git
cd speech-text-gpt-semdis
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Microphone Setup
Run the following script to identify the index of your preferred microphone:
```bash
python microphone-recognizer.py
```

Update the following variables in `idea_extractor.py` accordingly:
- `INPUT_DEVICE_INDEX`: your microphone device index
- `OPENAI_API_KEY_FILE`: name of the text file containing your OpenAI API key
- `GOOGLE_CLOUD_SPEECH_CREDENTIAL_FILE`: name of your Google Speech-to-Text credentials JSON file

> **Note**: These key files must be saved in the root of your project folder, or you’ll need to adjust the file paths accordingly.

---

## ▶️ Run the Tool

Start a full idea extraction session:
```bash
python idea_extractor.py
```

This will:
- Capture and transcribe real-time speech
- Use an LLM to extract realistic alternative uses
- Filter out duplicates
- Call SemDis to score novelty
- Live-plot idea ratings and annotate with extracted ideas
- Save transcripts and results

Press `ESC` to end the session and archive the data automatically.

---

## 📦 Features

- 🎙️ **Speech-to-text** via Google Cloud Speech
- 🧠 **LLM-powered idea extraction** (OpenAI GPT-4o-mini)
- 📊 **Novelty scoring** via [SemDis](https://cap.ist.psu.edu/semdis)
- 📈 **Live visualization** with annotated ideas
- 🗃️ **Automatic session archiving**

---

## 📂 Files Overview

| File | Description |
|------|-------------|
| `idea_extractor.py` | Main pipeline: speech → idea → plot |
| `semdis_api.py`     | Uploads idea pairs and downloads novelty scores |
| `plotter.py`        | Handles dynamic annotation + plotting |
| `microphone-recognizer.py` | Lists available microphones |

---

## 🗃️ Output Files

Each session generates:
- `idea_pairs.csv` — Task + extracted ideas
- `ratings.csv` — SemDis novelty ratings
- `transcripts.csv` — Raw transcripts
- A timestamped folder in `/data/` containing all of the above

---

## 🧪 Customization

You can modify:
- 🎯 The task (e.g. from “paperclip” to another item) in `TASK_ITEM`
- 💬 LLM extraction behavior in `send_to_chatgpt()`
- 🖼 Plot aesthetics in `plotter.py`
- 🎤 Audio input device in `INPUT_DEVICE_INDEX`

---

## 📄 License

MIT License
