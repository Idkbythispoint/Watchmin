#!/bin/bash
# Test runner script for Watchmin
# This script runs all tests without requiring API keys or secrets

echo "Running Watchmin Test Suite"
echo "=========================="
echo "Note: Tests are now configured to use mocked API clients"
echo "No API keys or secrets are required to run these tests."
echo ""

# Install dependencies if needed
pip install -r requirements.txt

# Run the test suite
python -m unittest discover tests/ -v

echo ""
echo "All tests completed!"
echo "To run specific test classes, use:"
echo "  python -m unittest tests.test.TestBaseFixer -v"
echo "  python -m unittest tests.test.TestToolsHandler -v" 
echo "  python -m unittest tests.test.TestBaseWatcher -v"
echo "  python -m unittest tests.test.TestMainFunctions -v"
echo "  python -m unittest tests.test.TestProcessFunctions -v"