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
