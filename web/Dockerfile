# Image cho web app (Django). Python 3.11 slim.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài dependency trước để tận dụng cache layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Khi dùng MySQL: bỏ comment dòng dưới + mở mysqlclient trong requirements.txt
# RUN apt-get update && apt-get install -y --no-install-recommends default-libmysqlclient-dev build-essential && rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

# Dev: chạy runserver. Production đổi sang gunicorn config.wsgi.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
