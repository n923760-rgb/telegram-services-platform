FROM python:3.12-slim AS app-base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/app
RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock && useradd -u 10001 -m app && mkdir -p /data/files && chown -R app:app /data
COPY --chown=app:app . .
USER app
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM app-base AS document-worker
USER root
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
USER app

FROM app-base AS app
