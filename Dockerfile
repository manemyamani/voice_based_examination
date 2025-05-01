FROM python:3.10-slim

# Install system dependencies for dlib
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-all-dev \
    libssl-dev \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy files into container
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port (Render uses PORT env variable)
EXPOSE 10000

# Start the app
CMD gunicorn app:app --bind 0.0.0.0:$PORT
