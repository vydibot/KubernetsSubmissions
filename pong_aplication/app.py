from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Counter stored in memory
request_counter = 0


class PongResponse(BaseModel):
    message: str


@app.get('/pingpong', response_model=PongResponse)
def ping():
    """Respond with pong and incrementing counter."""
    global request_counter
    request_counter += 1
    return PongResponse(message=f"pong {request_counter - 1}")


@app.get('/', response_model=PongResponse)
def root():
    """Root endpoint also returns pong."""
    global request_counter
    request_counter += 1
    return PongResponse(message=f"pong {request_counter - 1}")
