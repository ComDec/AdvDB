#!/bin/bash
# Run all test cases

echo "========================================"
echo "RepCRec - Run all test cases"
echo "========================================"
echo ""

# collect all test files
test_files=(test_*.txt)

# run each test
for test_file in "${test_files[@]}"; do
    echo "----------------------------------------"
    echo "运行: $test_file"
    echo "----------------------------------------"
    python main.py "$test_file"
    echo ""
    echo ""
done

echo "========================================"
echo "All tests completed!"
echo "========================================"
