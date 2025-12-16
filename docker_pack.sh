#!/bin/bash
# Script to package RepCRec using Docker
# This script handles the entire packaging process

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== RepCRec ReproZip Packaging via Docker ==="
echo ""

# Clean previous traces
echo "Cleaning previous traces..."
rm -rf .reprozip-trace repcrec.rpz

# Build Docker image with reprozip
echo "Building Docker image..."
docker build -t repcrec-pack . || {
    echo "Docker build failed. Trying alternative method..."
    echo "Using pre-built Python image with manual reprozip installation..."
    
    # Create a simpler Dockerfile on the fly
    cat > Dockerfile.simple << 'EOF'
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Try installing reprozip
RUN pip install --no-cache-dir reprozip reprounzip || \
    echo "ReproZip installation will be done manually"

WORKDIR /app
COPY *.py ./
COPY *.txt ./
COPY *.sh ./
RUN chmod +x *.sh 2>/dev/null || true
EOF
    
    docker build -f Dockerfile.simple -t repcrec-pack .
}

# Run packaging in container
echo "Running reprozip trace in container..."
docker run --rm \
    -v "$(pwd):/app" \
    -w /app \
    repcrec-pack \
    bash -c "
        if ! command -v reprozip &> /dev/null; then
            echo 'Installing reprozip...'
            pip install reprozip reprounzip || {
                echo 'Failed to install reprozip via pip'
                echo 'Please install reprozip manually in the container'
                exit 1
            }
        fi
        
        echo 'Tracing execution...'
        reprozip trace python3 main.py test_basic.txt
        
        echo 'Editing config to exclude packaging docs...'
        # Remove packaging documentation from config
        if [ -f .reprozip-trace/config.yml ]; then
            # Use sed to comment out or remove packaging doc files
            python3 << 'PYEOF'
import yaml
import sys

try:
    with open('.reprozip-trace/config.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Files to exclude
    exclude_patterns = [
        'REPROZIP', 'PACKAGING', 'Dockerfile', '.dockerignore',
        'pack_with_reprozip', 'reprozip_config_example'
    ]
    
    if 'other_files' in config:
        config['other_files'] = [
            f for f in config['other_files'] 
            if not any(pattern in f for pattern in exclude_patterns)
        ]
    
    with open('.reprozip-trace/config.yml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
except Exception as e:
    print(f'Config edit failed: {e}', file=sys.stderr)
    # Continue anyway
PYEOF
        fi
        
        echo 'Packing bundle...'
        reprozip pack repcrec.rpz
        
        echo 'Package created: repcrec.rpz'
        reprozip show repcrec.rpz | head -20
    "

echo ""
echo "=== Packaging Complete ==="
echo "Package file: repcrec.rpz"
echo ""
echo "To test the package:"
echo "  reprounzip directory setup repcrec.rpz test_dir"
echo "  reprounzip directory run test_dir python3 main.py test_basic.txt"

