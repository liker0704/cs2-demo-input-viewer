#!/bin/bash

# CS2 Input Visualizer - Test Runner
# Runs all test suites in order

set -e  # Exit on error

echo "======================================"
echo "CS2 Input Visualizer - Test Suite"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test and check result
run_test() {
    local test_name=$1
    local test_command=$2

    echo "Running: $test_name"
    echo "--------------------------------------"

    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED${NC}: $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}: $test_name"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# 1. Foundation Tests (Phase 1)
run_test "Foundation Tests" "python -m pytest tests/test_foundation.py -v --tb=short"

# 2. ETL Pipeline Tests (Phase 2)
run_test "ETL Pipeline Tests" "python test_etl_pipeline.py"

# 3. Network Layer Tests (Phase 4)
run_test "Network Layer Tests" "python test_network_layer.py"

# 4. Integration Tests (Phase 1-4)
run_test "Integration Tests" "python -m pytest tests/test_integration.py -v --tb=short"

# 5. All pytest tests together
run_test "All Pytest Tests" "python -m pytest tests/ -v --tb=short"

# Summary
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
