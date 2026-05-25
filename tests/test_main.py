import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_read_main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

import io
from unittest.mock import patch

@pytest.mark.asyncio
async def test_transcribe_endpoint():
    audio_content = b"fake audio data"
    
    with patch("src.main.client") as mock_client, patch("src.main.pyperclip.copy") as mock_copy:
        mock_client.audio.transcriptions.create.return_value.text = "Mocked transcription."
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            files = {"file": ("test.webm", io.BytesIO(audio_content), "audio/webm")}
            response = await ac.post("/transcribe", files=files)
            
        assert response.status_code == 200
        assert response.json() == {"text": "Mocked transcription."}
        mock_copy.assert_called_once_with("Mocked transcription.")
