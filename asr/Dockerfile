# Image cho service ASR (faster-whisper). Python 3.11 slim.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ASR_MODEL=base \
    ASR_MODEL_DIR=/models \
    ASR_LANG=en

WORKDIR /app

# ffmpeg: faster-whisper cần để giải mã audio webm/mp3 bé thu từ trình duyệt.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /models

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000

# Model tải về /models (mount volume) ở lần chạy đầu → không tải lại các lần sau.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
