#!/bin/sh

apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

pip install --progress-bar off --no-cache-dir -r /app/requirements.txt

uvicorn miniVGG_fastapi:app --host 0.0.0.0 --port 8001 --reload
