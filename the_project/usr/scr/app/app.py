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
    # Hardcoded todos list matching the exercise instructions
    todos = [
        "Learn Kubernetes basics",
        "Deploy application to cluster",
        "Configure persistent volumes"
    ]
    
    todos_html = "".join([f'<div style="background: white; padding: 15px; margin: 10px auto; width: 600px; border-left: 5px solid #2ecc71; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: left; font-size: 16px;">{todo}</div>' for todo in todos])

    return f"""
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Todo App</title>
      </head>
      <body style="font-family: Arial, sans-serif; background-color: #f4f4f9; text-align: center; margin: 0; padding: 20px;">
        <h1 style="color: #333; font-size: 36px;">Todo App</h1>
        
        <div style="margin: 20px 0;">
          <img src="/image" alt="Random Hourly Image" style="width: 300px; height: 300px; object-fit: cover; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />
        </div>

        <div style="margin: 30px 0;">
          <input type="text" maxlength="140" placeholder="Enter a new todo (max 140 characters)" style="width: 450px; padding: 12px; font-size: 14px; border: 1px solid #2ecc71; border-radius: 4px; outline: none;" />
          <button style="padding: 12px 24px; font-size: 14px; background-color: #2ecc71; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 8px; font-weight: bold;">Send</button>
        </div>

        <h2 style="color: #333; margin-top: 40px;">Todos</h2>
        <div style="display: flex; flex-direction: column; align-items: center;">
          {todos_html}
        </div>
      </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)