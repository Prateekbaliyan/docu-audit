FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (for OpenCV & Tesseract)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
