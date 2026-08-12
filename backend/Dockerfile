FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
EXPOSE 8080
CMD gunicorn --bind 0.0.0.0:${PORT:-8080} backend.app:app
