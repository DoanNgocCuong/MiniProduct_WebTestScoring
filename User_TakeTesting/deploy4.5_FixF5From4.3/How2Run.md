
### Run 1: main.py
- This project is simple and only uses Gradio library.
=> You can run directly by: `python main.py` (remember to install all libraries in `requirements.txt` file)

### Run 2: Docker

```bash
# Build the Docker image
docker build -t quiz-app .

# Run with docker-compose
docker-compose up -d
```







====================================================

#### Cách đóng gói Docker: 

I'll help you create a Docker configuration for your project. Based on your code structure and requirements, here's a recommended Dockerfile and related configuration:

1. First, create a `.dockerignore` file:

```text:.dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.git
.gitignore
.pytest_cache
*.log
```

2. Here's the optimized Dockerfile:

```dockerfile:Dockerfile
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
ENV GRADIO_SERVER_PORT=7860

# Create volumes for data persistence
VOLUME ["/app/data", "/app/out"]

# Expose port for Gradio interface
EXPOSE 7860

# Run the application
CMD ["python", "main.py"]
```

3. Create a `docker-compose.yml` file for easier deployment:

```yaml:docker-compose.yml
version: '3.8'

services:
  quiz-app:
    build: .
    ports:
      - "7860:7860"
    volumes:
      - ./data:/app/data
      - ./out:/app/out
    env_file:
      - .env
    restart: unless-stopped
```

To build and run the application using Docker, follow these steps:

1. Build the Docker image:
```bash
docker build -t quiz-app .
```

2. Run using docker-compose:
```bash
docker-compose up -d
```

Or run using Docker directly:
```bash
docker run -d -p 7860:7860 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/out:/app/out \
  quiz-app
```

Key features of this Docker configuration:

1. Uses Python 3.12 slim image for smaller size
2. Installs only necessary system dependencies
3. Creates persistent volumes for data and output
4. Sets proper environment variables for Gradio
5. Exposes port 7860 for the web interface
6. Mounts local data and out directories for persistence
7. Uses environment variables from .env file

Important notes:

1. Make sure your `data` directory contains the required Excel file (`Data_MarketingKit.xlsx`)
2. The `out` directory will store the results
3. The `.env` file should be present with your OpenAI API key and other credentials
4. Both directories should have proper permissions for Docker to read/write

This configuration provides a good balance between security, performance, and ease of use while maintaining data persistence through Docker volumes.