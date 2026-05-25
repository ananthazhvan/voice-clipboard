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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Clipboard</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #121212; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        #recordBtn { width: 120px; height: 120px; border-radius: 50%; background: #25D366; border: none; font-size: 1.2rem; font-weight: bold; color: white; margin-top: 50px; cursor: pointer; user-select: none; transition: transform 0.2s, background 0.2s; }
        #recordBtn.recording { background: #E53935; transform: scale(1.1); }
        #recordBtn.locked { background: #FFB300; transform: scale(1.1); }
        #status { margin-top: 20px; font-size: 1.1rem; min-height: 24px; color: #aaa; }
        #result { margin-top: 30px; font-size: 1.2rem; padding: 20px; background: #1e1e1e; border-radius: 10px; max-width: 80%; word-wrap: break-word; min-height: 50px; border: 1px solid #333; display: none; }
        .controls { margin-top: 40px; display: flex; align-items: center; gap: 10px; }
        .hint { font-size: 0.9rem; color: #777; margin-top: 10px; text-align: center; }
    </style>
</head>
<body>
    <h2>Hold to Speak</h2>
    <div class="hint">Slide up/away to lock for hands-free. Tap to stop.</div>
    <button id="recordBtn">Record</button>
    <div id="status">Ready</div>
    
    <div class="controls">
        <input type="checkbox" id="showToggle" checked>
        <label for="showToggle">Show transcriptions</label>
    </div>
    
    <div id="result"></div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;
        let isLocked = false;
        let startY = 0;
        
        const btn = document.getElementById('recordBtn');
        const status = document.getElementById('status');
        const result = document.getElementById('result');
        const showToggle = document.getElementById('showToggle');

        async function initAudio() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = async () => {
                    status.textContent = 'Transcribing...';
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    audioChunks = [];
                    
                    const formData = new FormData();
                    formData.append('file', audioBlob, 'recording.webm');
                    
                    try {
                        const response = await fetch('/transcribe', { method: 'POST', body: formData });
                        const data = await response.json();
                        if (showToggle.checked) {
                            result.textContent = data.text;
                            result.style.display = 'block';
                        }
                        status.textContent = 'Sent to clipboard!';
                        setTimeout(() => { status.textContent = 'Ready'; }, 3000);
                    } catch (e) {
                        status.textContent = 'Error: API failed';
                        status.style.color = '#E53935';
                    }
                };
            } catch (err) {
                status.textContent = 'Error: Microphone access denied';
                status.style.color = '#E53935';
            }
        }
        
        initAudio();

        function startRecording(e) {
            if (isRecording || !mediaRecorder) return;
            if (e.type && e.type.includes('touch')) startY = e.touches[0].clientY;
            else if (e.clientY) startY = e.clientY;
            
            isRecording = true;
            isLocked = false;
            audioChunks = [];
            mediaRecorder.start();
            btn.classList.add('recording');
            btn.textContent = 'Recording';
            status.textContent = 'Recording... Slide up to lock';
            result.style.display = 'none';
        }

        function stopRecording() {
            if (!isRecording) return;
            isRecording = false;
            isLocked = false;
            mediaRecorder.stop();
            btn.classList.remove('recording', 'locked');
            btn.textContent = 'Record';
        }

        function handleMove(e) {
            if (!isRecording || isLocked) return;
            let currentY = (e.type && e.type.includes('touch')) ? e.touches[0].clientY : e.clientY;
            if (startY - currentY > 50) {
                isLocked = true;
                btn.classList.remove('recording');
                btn.classList.add('locked');
                btn.textContent = 'Locked (Tap to Stop)';
                status.textContent = 'Recording locked';
            }
        }

        function handleEnd(e) {
            if (isRecording && !isLocked) stopRecording();
        }

        // Touch events for mobile
        btn.addEventListener('touchstart', startRecording);
        btn.addEventListener('touchmove', handleMove);
        btn.addEventListener('touchend', handleEnd);
        
        // Mouse events for desktop testing
        btn.addEventListener('mousedown', (e) => { startRecording(e); });
        window.addEventListener('mousemove', handleMove);
        window.addEventListener('mouseup', handleEnd);

        // Tap to stop when locked
        btn.addEventListener('click', () => { if (isLocked) stopRecording(); });
    </script>
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
