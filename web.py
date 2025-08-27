import asyncio
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

from sync import run_sync

app = FastAPI()

@app.get('/', response_class=HTMLResponse)
async def index():
    return """
    <html>
        <head>
            <title>fireTMS ↔ Optima Sync</title>
        </head>
        <body>
            <h1>fireTMS ↔ Optima Sync</h1>
            <button onclick=\"fetch('/run-sync',{method:'POST'}).then(r=>r.json()).then(d=>alert(d.status))\">Run sync</button>
        </body>
    </html>
    """

@app.post('/run-sync')
async def trigger_sync():
    asyncio.create_task(run_sync())
    return {"status": "started"}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
    )
