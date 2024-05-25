FROM python:3.9-slim-bullseye

WORKDIR /app

COPY requirements.txt /app/

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

RUN pip install --progress-bar off --no-cache-dir -r requirements.txt

COPY . /app/

VOLUME ./train/animals /app/train/animals

VOLUME ./predict/animals /app/predict/animals

VOLUME ./pickled_models /app/pickled_models

EXPOSE 8001

CMD ["uvicorn", "miniVGG_fastapi:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]