import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

SHARED_FILE_PATH = "/usr/src/app/shared/log.txt"

class StatusResponse(BaseModel):
    timestamp: str
    random_string: str

@app.get('/status', response_model=StatusResponse)
def get_status():
    """Read the latest logged string and timestamp from the shared file."""
    if not os.path.exists(SHARED_FILE_PATH):
        raise HTTPException(status_code=404, detail="Log file not found yet. Wait for writer to initialize.")
        
    try:
        with open(SHARED_FILE_PATH, "r") as f:
            lines = f.readlines()
            if not lines:
                raise HTTPException(status_code=503, detail="Log file is empty.")
            
            # Grab the latest line
            last_line = lines[-1].strip()
            
            # Parse the format "TIMESTAMP: UUID"
            timestamp, random_string = last_line.split(": ", 1)
            
            return StatusResponse(
                timestamp=timestamp,
                random_string=random_string
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)