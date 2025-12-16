# Dockerfile for RepCRec ReproZip Packaging
# This allows running ReproZip on macOS/Windows via Docker

FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including build tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    curl \
    wget \
    git \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install ReproZip from source (more reliable)
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir reprozip reprounzip || \
    (wget https://github.com/VIDA-NYU/reprozip/archive/refs/heads/main.zip -O /tmp/reprozip.zip && \
     cd /tmp && unzip reprozip.zip && cd reprozip-main && \
     pip3 install --no-cache-dir . && \
     pip3 install --no-cache-dir reprounzip)

# Set working directory
WORKDIR /app

# Copy project files
COPY *.py ./
COPY *.txt ./
COPY *.sh ./
COPY README.md ./
COPY REPROZIP_SETUP.md ./

# Make scripts executable
RUN chmod +x *.sh

# Default command: show help
CMD ["bash", "-c", "echo 'ReproZip environment ready. Use: reprozip trace python3 main.py test_basic.txt' && bash"]

