FROM python:3.11.4-slim

WORKDIR /usr/src/app

RUN apt update && apt upgrade -y && apt install -y curl && pip3 install --upgrade pip setuptools wheel && pip3 install poetry && poetry config virtualenvs.in-project false
COPY pyproject.toml poetry.lock gunicorn.conf.py ./
COPY api ./api
RUN poetry env use 3.11

RUN poetry install
HEALTHCHECK  --interval=15s --timeout=10s --start-period=7s \
  CMD curl --fail http://localhost:9876/health-check || exit 1
CMD poetry run gunicorn --access-logfile - --error-logfile - api.main:app_factory
