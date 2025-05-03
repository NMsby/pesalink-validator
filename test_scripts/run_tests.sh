#!/bin/bash

# Script to run comprehensive tests for the Bulk Account Validator

echo "PesaLink Bulk Account Validator - Test Suite"
echo "==========================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Create test directories if they don't exist
mkdir -p sample_data
mkdir -p test_output
mkdir -p logs

# Set color codes for better output readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to run a test and check its result
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "\n${YELLOW}Running Test: ${test_name}${NC}"
    echo "Command: $test_command"
    echo "-------------------------------------------"

    eval "$test_command"
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ Test Passed: ${test_name}${NC}"
    else
        echo -e "${RED}✗ Test Failed: ${test_name} (Exit Code: $exit_code)${NC}"
        failed_tests+=("$test_name")
    fi

    return $exit_code
}

# Array to store failed tests
failed_tests=()

# Test 1: API Integration Test
run_test "API Integration Test" "python test_scripts/test_pesalink_api.py --key --validate"

# Test 2: File Parser Test (with test data)
run_test "File Parser Test" "python -c \"
import sys
sys.path.append('.')
from app.utils.file_parser import FileParser
parser = FileParser()
accounts = parser.parse('sample_data/test_50_accounts.csv')
print(f'Parsed {len(accounts)} accounts')
assert len(accounts) > 0, 'Failed to parse accounts'
print('File parser test passed')
\""

# Test 3: PesaLink Data Handler Test
run_test "PesaLink Data Handler Test" "python -c \"
import sys, os
sys.path.append('.')
from app.utils.pesalink_data_handler import PesaLinkDataHandler
accounts = PesaLinkDataHandler.convert_to_accounts('sample_data/test_50_accounts.csv')
print(f'Converted {len(accounts)} accounts')
test_output = 'test_output/test_output.csv'
PesaLinkDataHandler.convert_to_csv(accounts, test_output)
print(f'Wrote accounts to {test_output}')
assert os.path.exists(test_output), 'Output file not created'
print('PesaLink data handler test passed')
\""

# Test 4: Basic Validation Test
run_test "Basic Validation Test" "python -m app.main --input sample_data/test_50_accounts.csv --output test_output --format json --verbose"

# Test 5: Parallel Validation Test
run_test "Parallel Validation Test" "python -m app.main --input sample_data/test_50_accounts.csv --output test_output --parallel --workers 4 --verbose"

# Test 6: PesaLink Format Test
run_test "PesaLink Format Test" "python -m app.main --input sample_data/test_50_accounts.csv --output test_output --pesalink --verbose"

# Test 7: Generate and Run Load Test (small scale)
run_test "Load Test" "python test_scripts/load_test.py --generate --accounts 100 --file test_output/load_test.csv --output test_output/load_test_results.csv --batch-sizes 50,100 --workers-list 2,4 --iterations 2"

# Test 8: Mock API Test (if mock API script exists)
if [ -f "test_scripts/mock_pesalink_api.py" ]; then
    # Start mock API in the background
    echo "Starting mock API server..."
    python test_scripts/mock_pesalink_api.py > logs/mock_api.log 2>&1 &
    MOCK_API_PID=$!

    # Wait for the server to start
    sleep 2

    # Run a test against the mock API
    PESALINK_API_BASE_URL="http://localhost:5000" run_test "Mock API Test" "python test_scripts/test_pesalink_api.py --validate --account 1234567890 --bank 01"

    # Kill the mock API server
    kill $MOCK_API_PID
else
    echo -e "${YELLOW}Skipping Mock API Test: Script not found${NC}"
fi

# Summary
echo -e "\n${YELLOW}Test Summary${NC}"
echo "==========================================="
# shellcheck disable=SC2320
echo "Total Tests: $((${#failed_tests[@]} + $?))"
# shellcheck disable=SC2320
echo "Passed Tests: $(($? - ${#failed_tests[@]}))"
echo "Failed Tests: ${#failed_tests[@]}"

if [ ${#failed_tests[@]} -gt 0 ]; then
    echo -e "\n${RED}Failed Tests:${NC}"
    for test in "${failed_tests[@]}"; do
        echo "- $test"
    done
    exit 1
else
    echo -e "\n${GREEN}All tests passed successfully!${NC}"
    exit 0
fi