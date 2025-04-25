# This is a temporary file right now it will not work for this project

# Build from python slim image
FROM python:3.13-slim

# Set ENV variables
ENV TZ=America/New_York
ENV DEBIAN_FRONTEND=noninteractive

# Default display to :99
ENV DISPLAY=:99

# Install other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    dos2unix \
    python3-pip \ 
    git \
    tzdata \
    xvfb \
    pm2 \
    ffmpeg \
    streamlink \
&& rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# CD into app
WORKDIR /app
COPY . .

# Make the entrypoint executable
RUN dos2unix entrypoint.sh && \
    chmod +x entrypoint.sh

# Set the entrypoint to our entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
