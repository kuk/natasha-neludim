FROM python:3.9.13-slim

RUN pip install --no-cache-dir \
    aiogram==2.21 \
    aiobotocore==2.3.4

COPY main.py .
CMD python main.py
