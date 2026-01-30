# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (ca-certificates for HTTPS/Firebase)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose WebSocket port
EXPOSE 5557

# Set environment variables
ENV MUD_BIND_ADDRESS=0.0.0.0
ENV MUD_WEBSOCKET_PORT=5557
ENV PYTHONUNBUFFERED=1

# Run the server
CMD ["python3", "mud_server.py"]
