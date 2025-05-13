FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=host.docker.internal:0.0

# Install system dependencies for Tkinter GUI and OpenCV
RUN apt-get update && apt-get install -y \
    xvfb \
    tk \
    python3-tk \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for data
RUN mkdir -p logs results

# Set environment variable for path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/app.py"] 