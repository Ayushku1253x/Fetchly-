FROM python:3.12-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD sh -c "pip install -U yt-dlp && gunicorn -b 0.0.0.0:${PORT:-10000} -t 600 app:app"
