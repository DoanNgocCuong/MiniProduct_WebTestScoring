# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend_package/ ./backend_package/
COPY frontend_package/ ./frontend_package/
COPY main.py .
COPY config.py .

# Create directories for data and output
RUN mkdir -p /app/data /app/out

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=PORT

# Create volumes for data persistence
VOLUME ["/app/data", "/app/out"]

# Expose port for Gradio interface
EXPOSE 25008

# Run the application
CMD ["python", "main.py"]