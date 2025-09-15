FROM python:3.11-slim

WORKDIR /app

# Copy only what's needed for docs server
COPY api/docs_server.py /app/api/docs_server.py
COPY docs /app/docs
COPY media /app/media

RUN pip install --no-cache-dir fastapi==0.112.* uvicorn[standard]==0.30.*

EXPOSE 8808

CMD ["uvicorn", "api.docs_server:app", "--host", "0.0.0.0", "--port", "8808"]
