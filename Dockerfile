FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
        fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir paho-mqtt requests pillow

COPY fetch_bambu.py camera.py ./

ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "fetch_bambu.py"]
