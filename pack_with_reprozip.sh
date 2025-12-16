#!/bin/bash
# Automated ReproZip packaging script for RepCRec
# Usage: ./pack_with_reprozip.sh [test_file]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== RepCRec ReproZip Packaging Script ===${NC}\n"

# Check if reprozip is installed
if ! command -v reprozip &> /dev/null; then
    echo -e "${RED}Error: reprozip not found!${NC}"
    echo "Please install reprozip first:"
    echo "  conda install -c conda-forge reprozip reprounzip"
    echo "  or"
    echo "  pip install reprozip reprounzip"
    echo ""
    echo "Alternatively, use Docker:"
    echo "  docker build -t repcrec-pack ."
    echo "  docker run -it -v \$(pwd):/app repcrec-pack"
    exit 1
fi

# Clean previous traces and packages
echo -e "${YELLOW}Cleaning previous traces and packages...${NC}"
rm -rf .reprozip-trace repcrec.rpz

# Determine what to trace
TEST_FILE="${1:-test_basic.txt}"

if [ -f "$TEST_FILE" ]; then
    echo -e "${GREEN}Tracing execution with test file: $TEST_FILE${NC}"
    reprozip trace python3 main.py "$TEST_FILE"
elif [ -f "run_all_tests.sh" ]; then
    echo -e "${GREEN}Tracing execution with all tests...${NC}"
    reprozip trace ./run_all_tests.sh
else
    echo -e "${YELLOW}No test file specified, tracing basic execution...${NC}"
    echo "begin(T1)" | reprozip trace python3 main.py
fi

# Show configuration
echo -e "\n${GREEN}Configuration captured:${NC}"
reprozip show config.yml | head -30

# Ask if user wants to edit
echo -e "\n${YELLOW}Do you want to edit the configuration? (y/n)${NC}"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    reprozip edit config.yml
fi

# Pack the bundle
echo -e "\n${GREEN}Packing ReproZip bundle...${NC}"
reprozip pack repcrec.rpz

# Show package info
echo -e "\n${GREEN}Package created: repcrec.rpz${NC}"
echo -e "${GREEN}Package contents:${NC}"
reprozip show repcrec.rpz | head -20

# Test unpacking
echo -e "\n${YELLOW}Testing unpacking...${NC}"
rm -rf test_unpack
reprounzip directory setup repcrec.rpz test_unpack

echo -e "\n${GREEN}✓ Package created successfully!${NC}"
echo -e "\nTo use the package:"
echo "  1. Directory unpack: reprounzip directory setup repcrec.rpz run_dir"
echo "  2. Docker: reprounzip dockerfile repcrec.rpz && docker build -t repcrec ."
echo "  3. Vagrant: reprounzip vagrant setup repcrec.rpz"

