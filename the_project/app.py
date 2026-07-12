import os
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    port = os.getenv("PORT", "8000")
    print(f"Server started in port {port}")
    yield


app = FastAPI(title="Todo App", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Todo app is running"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
