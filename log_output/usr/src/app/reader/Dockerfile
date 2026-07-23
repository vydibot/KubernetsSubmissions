# Use a lightweight Python base image
FROM python:3.11-slim

WORKDIR /usr/src/app

RUN pip install --no-cache-dir fastapi uvicorn pydantic httpx

COPY reader.py .

EXPOSE 5000

# Start the FastAPI server using Uvicorn
CMD ["uvicorn", "reader:app", "--host", "0.0.0.0", "--port", "5000"]