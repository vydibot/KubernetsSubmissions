import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

SHARED_DIR = "/usr/src/app/shared"
LOG_FILE_PATH = os.path.join(SHARED_DIR, "log.txt")
PING_FILE_PATH = os.path.join(SHARED_DIR, "pingpong.txt")

class StatusResponse(BaseModel):
    timestamp: str
    random_string: str
    pingpong_count: int

@app.get('/status', response_model=StatusResponse)
def get_status():
    # 1. Read timestamp and random string from log.txt
    if not os.path.exists(LOG_FILE_PATH):
        raise HTTPException(status_code=404, detail="Log file not found yet.")
        
    with open(LOG_FILE_PATH, "r") as f:
        lines = f.readlines()
        if not lines:
            raise HTTPException(status_code=503, detail="Log file is empty.")
        last_line = lines[-1].strip()
        timestamp, random_string = last_line.split(": ", 1)

    # 2. Read ping-pong count from pingpong.txt
    pingpong_count = 0
    if os.path.exists(PING_FILE_PATH):
        try:
            with open(PING_FILE_PATH, "r") as f:
                content = f.read().strip()
                pingpong_count = int(content) if content else 0
        except Exception:
            pingpong_count = 0

    return StatusResponse(
        timestamp=timestamp,
        random_string=random_string,
        pingpong_count=pingpong_count
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)