FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libasound2-dev \
        libportmidi-dev \
        libfreetype6-dev \
        libsdl2-dev \
        libsdl2-image-dev \
        libsdl2-mixer-dev \
        libsdl2-ttf-dev \
        libx11-dev \
        x11-xserver-utils \
        git \
        curl \
        wget && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY clock/ /app
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy entire app source into the container
COPY plantangenet/ /lib/plantangenet/python

# Install plantangenet in editable mode
RUN pip install -e /lib/plantangenet/python

# Set default command (can be overridden by docker-compose)
CMD ["bash"]
