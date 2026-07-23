import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI()

SHARED_DIR = "/usr/src/app/shared"
LOG_FILE_PATH = os.path.join(SHARED_DIR, "log.txt")

# Kubernetes DNS service URL (Fallback to Cluster IP or Env Var if needed)
PONG_SERVICE_URL = os.getenv("PONG_SERVICE_URL", "http://pong-app-svc:2346/pongs")

class StatusResponse(BaseModel):
    timestamp: str
    random_string: str
    pingpong_count: int

def fetch_latest_log():
    if not os.path.exists(LOG_FILE_PATH):
        raise HTTPException(status_code=404, detail="Log file not found yet.")
        
    with open(LOG_FILE_PATH, "r") as f:
        lines = f.readlines()
        if not lines:
            raise HTTPException(status_code=503, detail="Log file is empty.")
        last_line = lines[-1].strip()
        timestamp, random_string = last_line.split(": ", 1)
        return timestamp, random_string

async def fetch_ping_count() -> int:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(PONG_SERVICE_URL, timeout=3.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("pongs", 0)
    except Exception as e:
        print(f"Error fetching pongs from {PONG_SERVICE_URL}: {e}")
    return 0

@app.get('/', response_class=PlainTextResponse)
async def get_root():
    timestamp, random_string = fetch_latest_log()
    pingpong_count = await fetch_ping_count()
    return f"{timestamp}: {random_string}.\nPing / Pongs: {pingpong_count}"

@app.get('/status', response_model=StatusResponse)
async def get_status():
    timestamp, random_string = fetch_latest_log()
    pingpong_count = await fetch_ping_count()

    return StatusResponse(
        timestamp=timestamp,
        random_string=random_string,
        pingpong_count=pingpong_count
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)