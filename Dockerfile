FROM python:3.11

# Prevent .pyc files + enable stdout logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /opt/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=fishmouth.wsgi:app

CMD \
    gunicorn --bind "0.0.0.0:${P_PORT:-5000}" ${FLASK_APP}
