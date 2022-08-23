FROM python:3.9.13-slim

RUN pip install --no-cache-dir \
    aiohttp==3.8.1 \
    aiogram==2.21 \
    aiobotocore==2.3.4

COPY main.py .

# Exec form is required, otherwise args are ignored
# https://docs.docker.com/engine/reference/builder/#exec-form-entrypoint-example
ENTRYPOINT ["python", "main.py"]
