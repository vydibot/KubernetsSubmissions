import time
import uuid
import threading
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

# Store the random string in memory
RANDOM_VALUE = str(uuid.uuid4())


class StatusResponse(BaseModel):
    timestamp: str
    random_string: str


def format_timestamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@app.get('/status', response_model=StatusResponse)
def get_status():
    """Return the current status with timestamp and random string."""
    timestamp = format_timestamp(datetime.now(timezone.utc))
    return StatusResponse(
        timestamp=timestamp,
        random_string=RANDOM_VALUE
    )


def logger_task() -> None:
    """Background task that logs the timestamp and random value."""
    try:
        while True:
            timestamp = format_timestamp(datetime.now(timezone.utc))
            print(f"{timestamp}: {RANDOM_VALUE}", flush=True)
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopping logger.", flush=True)


def main() -> None:
    # Start the logger as a background thread
    logger_thread = threading.Thread(target=logger_task, daemon=True)
    logger_thread.start()


if __name__ == "__main__":
    # Note: Run with uvicorn: uvicorn app:app --host 0.0.0.0 --port 5000
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
