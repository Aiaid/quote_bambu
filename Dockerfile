FROM mwader/static-ffmpeg:8.1@sha256:6fb848850b647688910ccf88112a96afe5ee46bcd54ee41daf875cac98b02bff AS ffmpeg

FROM python:3.12-alpine

COPY --from=ffmpeg /ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg /doc /usr/share/doc/ffmpeg/html
COPY --from=ffmpeg /versions.json /usr/share/doc/ffmpeg/versions.json

RUN apk add --no-cache \
        ca-certificates \
        tzdata \
        font-dejavu

WORKDIR /app

COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY fetch_bambu.py camera.py quote0_canvas.py ./
COPY LICENSE THIRD_PARTY_NOTICES.md /usr/share/licenses/quote-bambu/
COPY LICENSES /usr/share/licenses/quote-bambu/LICENSES

ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "fetch_bambu.py"]
