FROM python:3.10-slim

WORKDIR /solar_app

COPY solar_germany /solar_app/solar_germany

COPY .env /solar_app/.env

COPY requirements.txt /solar_app/requirements.txt

RUN pip install --upgrade pip && pip install --no-cache-dir -r /solar_app/requirements.txt

ENV PORT=8501

CMD uvicorn brainmap.api.fast:app --host 0.0.0.0 --port $PORT
