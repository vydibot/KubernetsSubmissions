import os
import time
import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse

# Directory where the persistent volume will store the image
IMAGE_DIR = os.getenv("IMAGE_DIR", "usr/src/app/images")
IMAGE_PATH = os.path.join(IMAGE_DIR, "cached_image.jpg")
CACHE_DURATION = 600  # 10 minutes in seconds


async def fetch_and_cache_image():
    """Fetches a new image from Lorem Picsum and saves it to the persistent volume."""
    os.makedirs(IMAGE_DIR, exist_ok=True)
    url = "https://picsum.photos/1200"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        if response.status_code == 200:
            with open(IMAGE_PATH, "wb") as f:
                f.write(response.content)


@asynccontextmanager
async def lifespan(app: FastAPI):
    port = os.getenv("PORT", "8000")
    print(f"Server started in port {port}")
    
    # Ensure directory exists and download an initial image if none exists
    os.makedirs(IMAGE_DIR, exist_ok=True)
    if not os.path.exists(IMAGE_PATH):
        try:
            await fetch_and_cache_image()
        except Exception as e:
            print(f"Failed to fetch initial image: {e}")
            
    yield


app = FastAPI(title="Todo App", lifespan=lifespan)


@app.get("/image")
async def get_image():
    """Serves the cached image, refreshing it if 10 minutes have passed."""
    if os.path.exists(IMAGE_PATH):
        file_age = time.time() - os.path.getmtime(IMAGE_PATH)
        if file_age > CACHE_DURATION:
            try:
                await fetch_and_cache_image()
            except Exception as e:
                print(f"Failed to update cached image: {e}")
    else:
        try:
            await fetch_and_cache_image()
        except Exception as e:
            print(f"Failed to fetch image: {e}")

    if os.path.exists(IMAGE_PATH):
        return FileResponse(IMAGE_PATH, media_type="image/jpeg")
    
    return {"error": "Image not available"}, 404


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Todo App</title>
      </head>
      <body>
        <h1>Todo App</h1>
        <p>The app is running inside Kubernetes.</p>
        <div style="margin-top: 20px;">
          <img src="/image" alt="Random Hourly Image" style="max-width: 100%; height: auto; border-radius: 8px;" />
        </div>
      </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)