FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=host.docker.internal:0.0

# Install system dependencies for OpenCV, Tkinter, and geo analysis
RUN apt-get update && apt-get install -y \
    xvfb \
    tk \
    python3-tk \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgtk-3-0 \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libpango-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    flask==2.3.3 \
    openai==1.40.0 \
    httpx==0.25.0 \
    python-dotenv==1.0.0 \
    requests==2.31.0 \
    Pillow==9.5.0 \
    waitress==2.1.2 \
    opencv-python==4.8.0.74 \
    numpy==1.24.3 \
    geojson==3.0.1

# Create application directory structure (will be mounted from host)
RUN mkdir -p logs results missions

# Set environment variable for path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Default command (src/app.py will be mounted from host)
CMD ["python", "src/app.py"] 