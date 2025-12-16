#!/bin/bash
echo "========================================"
echo "RepCRec - run all tests"
echo "========================================"
echo ""

test_files=(test_*.txt)

for test_file in "${test_files[@]}"; do
    echo "----------------------------------------"
    echo "Running: $test_file"
    echo "----------------------------------------"
    python main.py "$test_file"
    echo ""
    echo ""
done

echo "========================================"
echo "All tests done!"
echo "========================================"
