FROM python:3.11-slim

WORKDIR /app

# Install factory dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    requests \
    python-dotenv \
    pydantic

# Copy application code
COPY factory/ /app/factory/
COPY modules/blue_realtime.py /app/modules/blue_realtime.py
COPY modules/blue_memory.py /app/modules/blue_memory.py
COPY modules/__init__.py /app/modules/__init__.py
COPY utils/ /app/utils/

# Create data directories
RUN mkdir -p /data/overlays /data/releases

EXPOSE 8400

CMD ["uvicorn", "factory.api.server:app", "--host", "0.0.0.0", "--port", "8400"]
