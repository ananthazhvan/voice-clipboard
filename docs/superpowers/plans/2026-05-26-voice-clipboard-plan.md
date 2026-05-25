# Voice-to-Clipboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-network web service that records audio from a phone browser, transcribes it via Groq Whisper API, and copies the text to the laptop's clipboard.

**Architecture:** A FastAPI Python backend running locally, serving a single-page HTML frontend. The frontend uses `MediaRecorder` to capture audio and POSTs it to the backend. The backend uses the official `groq` Python client to transcribe the audio and `pyperclip` to manage the clipboard.

**Tech Stack:** Python 3, FastAPI, Uvicorn, Groq API, Pyperclip, Pytest, HTML5, Vanilla JS (MediaRecorder).

---

### Task 1: Project Setup & Base Server

**Files:**
- Create: `requirements.txt`
- Create: `src/main.py`
- Create: `tests/test_main.py`
- Create: `.env.example`

- [ ] **Step 1: Write dependencies and env file**

```text
fastapi==0.111.0
uvicorn==0.29.0
python-multipart==0.0.9
pyperclip==1.8.2
groq==0.8.0
python-dotenv==1.0.1
pytest==8.2.0
httpx==0.27.0
pytest-asyncio==0.23.6
```

```text
GROQ_API_KEY=your_api_key_here
```

- [ ] **Step 2: Write the failing test for base route**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_read_main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_main.py -v`
Expected: FAIL with ModuleNotFoundError: No module named 'src'

- [ ] **Step 4: Write minimal implementation for base route**

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example src/main.py tests/test_main.py
git commit -m "feat: setup basic fastapi server and tests"
```

### Task 2: Backend Transcription Endpoint

**Files:**
- Modify: `tests/test_main.py:10-30`
- Modify: `src/main.py:18-40`

- [ ] **Step 1: Write the failing test for `/transcribe` endpoint**

```python
import io
from unittest.mock import patch

@pytest.mark.asyncio
async def test_transcribe_endpoint():
    audio_content = b"fake audio data"
    
    # We mock Groq client and pyperclip so we don't actually hit the API or clipboard in tests
    with patch("src.main.Groq") as mock_groq_class, patch("src.main.pyperclip.copy") as mock_copy:
        mock_client = mock_groq_class.return_value
        mock_client.audio.transcriptions.create.return_value.text = "Mocked transcription."
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"file": ("test.webm", io.BytesIO(audio_content), "audio/webm")}
            response = await ac.post("/transcribe", files=files)
            
        assert response.status_code == 200
        assert response.json() == {"text": "Mocked transcription."}
        mock_copy.assert_called_once_with("Mocked transcription.")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_transcribe_endpoint -v`
Expected: FAIL with 404 Not Found (since `/transcribe` doesn't exist).

- [ ] **Step 3: Write minimal implementation**

Modify `src/main.py` to add the endpoint, groq client setup, and pyperclip logic.

```python
import os
import pyperclip
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

client = Groq(api_key=os.environ.get("GROQ_API_KEY", "dummy"))

# ... (keep existing read_root and html_content) ...

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/main.py tests/test_main.py
git commit -m "feat: add transcribe endpoint with groq and pyperclip"
```

### Task 3: Frontend UI and Audio Recording

**Files:**
- Modify: `src/main.py:6-18` (Replacing `html_content` string with full JS app)

- [ ] **Step 1: Write the full HTML/JS frontend**

Replace `html_content` in `src/main.py` with the following implementation. Since TDD for complex vanilla JS MediaRecorder flows is hard in simple Pytest, we implement directly and verify manually.

```python
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
            if (e.type.includes('touch')) startY = e.touches[0].clientY;
            
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
            let currentY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
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
        btn.addEventListener('mousedown', (e) => { startY = e.clientY; startRecording(e); });
        window.addEventListener('mousemove', handleMove);
        window.addEventListener('mouseup', handleEnd);

        // Tap to stop when locked
        btn.addEventListener('click', () => { if (isLocked) stopRecording(); });
    </script>
</body>
</html>
"""
```

- [ ] **Step 2: Run test to verify basic route still passes**

Run: `pytest tests/test_main.py::test_read_main -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: add frontend ui with mediarecorder and slide-to-lock"
```
