FROM python:3.9.13-slim

COPY requirements requirements
RUN pip install --disable-pip-version-check --no-cache-dir -r requirements/main.txt

COPY neludim neludim
COPY setup.py .
RUN pip install --disable-pip-version-check --no-cache-dir -e .

# Exec form is required, otherwise args are ignored
# https://docs.docker.com/engine/reference/builder/#exec-form-entrypoint-example
ENTRYPOINT ["neludim"]
