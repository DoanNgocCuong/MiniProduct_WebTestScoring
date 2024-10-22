
# `dockerignore` is like `.gitignore` - it tells Docker which files/directories to exclude when copying files into the container. Here's a recommended `.dockerignore`  for your project:

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

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

# Tạo volume cho thư mục out
# - `Volume` trong Docker: Dòng `# Tạo volume cho thư mục out` trong Dockerfile có nghĩa là tạo một `volume`  cho thư mục `out`. 
# Volume là một cách để lưu trữ dữ liệu bên ngoài container. Dữ liệu trong `volume` sẽ không bị mất khi container bị xóa hoặc tái tạo.
# Volume cho phép bạn chia sẻ dữ liệu giữa nhiều container hoặc giữa container và máy chủ (host).
VOLUME /app/out

# Expose port for Gradio interface
EXPOSE 7860

# Run the application
CMD ["python", "main.py"]



# # Build image
# docker build -t quiz-app .

# # Chạy container
# docker run -p 7860:7860 \
#   --env-file .env \
#   -v $(pwd)/out:/app/out \ 
#   quiz-app