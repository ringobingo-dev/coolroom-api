#!/bin/bash
set -e

echo "🧪 Running all tests..."

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v --html=test-reports/unit-test-report.html

# Run integration tests
echo "Running integration tests..."
python -m pytest tests/integration/ -v --html=test-reports/integration-test-report.html

# Run load tests
echo "Running load tests..."
python tests/load/test_performance.py > test-reports/load-test-report.txt

echo "✅ All tests completed!"
echo "Test reports available in test-reports directory"
