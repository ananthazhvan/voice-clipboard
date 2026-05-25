import os
import pyperclip
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

client = Groq(api_key=os.environ.get("GROQ_API_KEY", "dummy"))

html_content = """
<!DOCTYPE html>
<html>
    <head>
        <title>Voice Clipboard</title>
    </head>
    <body>
        <h1>Voice Clipboard</h1>
    </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return html_content

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    # Read audio bytes
    audio_bytes = await file.read()
    
    # Transcribe via Groq API
    transcription = client.audio.transcriptions.create(
        file=(file.filename, audio_bytes),
        model="whisper-large-v3-turbo",
    )
    
    # Copy to clipboard
    text = transcription.text
    pyperclip.copy(text)
    
    return {"text": text}
