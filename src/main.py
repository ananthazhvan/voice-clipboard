import os
import pyperclip
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

client = Groq(api_key=os.environ.get("GROQ_API_KEY", "dummy"))

HISTORY_FILE = "history.txt"

html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Clipboard</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #121212; color: white; display: flex; flex-direction: column; align-items: center; padding: 20px; margin: 0; }
        #recordBtn { width: 120px; height: 120px; border-radius: 50%; background: #25D366; border: none; font-size: 1.2rem; font-weight: bold; color: white; margin-top: 20px; cursor: pointer; user-select: none; transition: transform 0.2s, background 0.2s; }
        #recordBtn.recording { background: #E53935; transform: scale(1.1); }
        #recordBtn.locked { background: #FFB300; transform: scale(1.1); }
        #status { margin-top: 20px; font-size: 1.1rem; min-height: 24px; color: #aaa; }
        #result { margin-top: 20px; font-size: 1.2rem; padding: 20px; background: #1e1e1e; border-radius: 10px; max-width: 90%; word-wrap: break-word; min-height: 20px; border: 1px solid #333; display: none; }
        .controls { margin-top: 20px; display: flex; align-items: center; gap: 10px; }
        .hint { font-size: 0.9rem; color: #777; margin-top: 10px; text-align: center; }
        #historyContainer { margin-top: 40px; width: 100%; max-width: 400px; }
        #historyContainer h3 { color: #888; border-bottom: 1px solid #333; padding-bottom: 10px; }
        .history-item { background: #1e1e1e; padding: 15px; margin-bottom: 10px; border-radius: 8px; font-size: 1rem; color: #ccc; }
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

    <div id="historyContainer">
        <h3>Recent Transcriptions</h3>
        <div id="historyList"></div>
    </div>

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
        const historyList = document.getElementById('historyList');

        async function fetchHistory() {
            try {
                const res = await fetch('/api/history');
                const data = await res.json();
                historyList.innerHTML = data.history.reverse().map(item => `<div class="history-item">${item}</div>`).join('');
            } catch (e) {
                console.error("Failed to load history");
            }
        }

        async function initAudio() {
            fetchHistory();
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
                        fetchHistory(); // Refresh history
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

        btn.addEventListener('touchstart', startRecording);
        btn.addEventListener('touchmove', handleMove);
        btn.addEventListener('touchend', handleEnd);
        
        btn.addEventListener('mousedown', (e) => { startRecording(e); });
        window.addEventListener('mousemove', handleMove);
        window.addEventListener('mouseup', handleEnd);

        btn.addEventListener('click', () => { if (isLocked) stopRecording(); });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return html_content

@app.get("/api/history")
async def get_history():
    if not os.path.exists(HISTORY_FILE):
        return {"history": []}
    with open(HISTORY_FILE, "r") as f:
        lines = f.readlines()
    return {"history": [line.strip() for line in lines if line.strip()]}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    
    transcription = client.audio.transcriptions.create(
        file=(file.filename, audio_bytes),
        model="whisper-large-v3-turbo",
    )
    
    text = transcription.text
    pyperclip.copy(text)
    
    # Save to history
    with open(HISTORY_FILE, "a") as f:
        f.write(text + "\\n")
        
    return {"text": text}

