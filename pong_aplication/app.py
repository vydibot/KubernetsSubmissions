from fastapi import FastAPI

app = FastAPI()

# Store counter in memory
counter = 0

@app.get("/pingpong")
def pingpong():
    global counter
    counter += 1
    return f"pong {counter}"

@app.get("/pongs")
def get_pongs():
    return {"pongs": counter}

@app.get("/")
def root():
    return pingpong()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)