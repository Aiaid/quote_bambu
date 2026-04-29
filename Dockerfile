FROM mwader/static-ffmpeg:7.1 AS ffmpeg

FROM python:3.12-alpine

COPY --from=ffmpeg /ffmpeg /usr/local/bin/ffmpeg

RUN apk add --no-cache \
        ca-certificates \
        tzdata \
        font-dejavu

WORKDIR /app

RUN pip install --no-cache-dir paho-mqtt requests pillow

COPY fetch_bambu.py camera.py ./

ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "fetch_bambu.py"]
