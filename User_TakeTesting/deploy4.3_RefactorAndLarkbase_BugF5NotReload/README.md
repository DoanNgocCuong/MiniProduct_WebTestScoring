
### How to run? 
- Không như các project có nhiều library, Project này rất đơn giản chỉ xài: Gradio. 
=> You can run directly by: `python main.py` (remember to install all libraries in `requirements.txt` file)

### Other options to run with DOCKER: How to build docker image? 

Ver 1: 
```bash
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 25008 available to the world outside this container
EXPOSE 25008

# Define environment variable
ENV NAME World

# Run main.py when the container launches
CMD ["python", "main.py"]
```

Ver 2: 
```bash

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

```
- Đảm bảo rằng cả hai thư mục `data` và `out` đã tồn tại trên máy chủ trước khi chạy lệnh.
- Sử dụng `mount`: Bất kỳ thay đổi nào trong thư mục `data` trên máy chủ sẽ được phản ánh ngay lập tức trong container, và kết quả sẽ được lưu vào thư mục `out` trên máy chủ (được lưu trữ ngay cả khi container bị xaá).
```bash
docker run -p 7860:7860 \
  --env-file .env \
  -v $(pwd)/data:/app/data \  # Mount thư mục data
  -v $(pwd)/out:/app/out \    # Mount thư mục out
  quiz-app
```