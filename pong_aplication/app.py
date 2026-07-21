import os
from fastapi import FastAPI

app = FastAPI()
SHARED_FILE_PATH = "/usr/src/app/shared/pingpong.txt"

def get_count() -> int:
    if not os.path.exists(SHARED_FILE_PATH):
        return 0
    try:
        with open(SHARED_FILE_PATH, "r") as f:
            content = f.read().strip()
            return int(content) if content else 0
    except Exception:
        return 0

def save_count(count: int) -> None:
    os.makedirs(os.path.dirname(SHARED_FILE_PATH), exist_ok=True)
    with open(SHARED_FILE_PATH, "w") as f:
        f.write(str(count))

@app.get("/ping")
def ping():
    count = get_count() + 1
    save_count(count)
    return f"pong {count}"

@app.get("/")
def root():
    return ping()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)