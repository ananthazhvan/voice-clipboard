# Voice Clipboard

A local-network web service that lets you record your voice on your phone browser, instantly transcribe it using Groq's high-speed Whisper API, and paste the text directly into your laptop's clipboard.

## Features
- **Hold to Speak:** WhatsApp-style microphone interaction.
- **Slide to Lock:** Slide up for hands-free recording.
- **Instant Transcription:** Powered by Groq `whisper-large-v3-turbo` for near-instant results.
- **Direct Clipboard Integration:** The transcribed text is automatically injected into the laptop clipboard.

## Requirements
- Python 3.10+
- A Groq API Key (Free tier works perfectly)
- A local network connection (e.g. laptop connected to phone's hotspot)

## Setup

1. **Clone and Install:**
```bash
git clone https://github.com/ananthazhvan/voice-clipboard.git
cd voice-clipboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure API Key:**
Copy `.env.example` to `.env` and paste your Groq API key:
```env
GROQ_API_KEY=your_api_key_here
```

3. **Run the Server:**
```bash
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 5000
```

## How to Use It

1. **Find your Laptop's IP:** 
   Find your local IP on the hotspot network (usually looks like `192.168.x.x` or `10.x.x.x`). On Linux, run `ip a`.
2. **Open on Phone:** 
   Make sure your laptop is connected to your phone's hotspot. Open your phone's web browser and go to `http://<YOUR_LAPTOP_IP>:5000`.
3. **Record:** 
   Press and hold the Green Mic button to talk. Release it to stop recording. (Or slide up to lock it for hands-free recording!).
4. **Paste:** 
   The transcribed text is automatically pushed into your laptop's clipboard. Hit `Ctrl+V` anywhere on your laptop!
