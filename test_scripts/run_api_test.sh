#!/bin/bash

# Script to test the PesaLink API integration

echo "PesaLink API Integration Test Runner"
echo "===================================="

# Check for Python
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check for required packages
python -c "import requests" 2>/dev/null
# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip install requests python-dotenv
fi

# Create .env file with API base URL if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "PESALINK_API_BASE_URL=https://account-validation-service.dev.pesalink.co.ke" > .env
    echo "Created .env file with default API URL"
fi

# Process command line arguments
VERBOSE=""
API_KEY_TEST=false
VALIDATE_TEST=false
ACCOUNT_NUMBER="123456789"
BANK_CODE="ABC"
BATCH_TEST=false
BATCH_SIZE=5
DOWNLOAD_TEST=false
SAMPLE_NAME="sample_1000"

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE="--verbose"
            shift
            ;;
        --key)
            API_KEY_TEST=true
            shift
            ;;
        --validate)
            VALIDATE_TEST=true
            shift
            ;;
        --account)
            ACCOUNT_NUMBER="$2"
            shift 2
            ;;
        --bank)
            BANK_CODE="$2"
            shift 2
            ;;
        --batch)
            BATCH_TEST=true
            shift
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --download)
            DOWNLOAD_TEST=true
            shift
            ;;
        --sample)
            SAMPLE_NAME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --verbose, -v     Enable verbose logging"
            echo "  --key             Test API key retrieval"
            echo "  --validate        Test account validation"
            echo "  --account NUM     Account number to validate (default: 123456789)"
            echo "  --bank CODE       Bank code for validation (default: ABC)"
            echo "  --batch           Test batch validation"
            echo "  --batch-size N    Number of accounts in test batch (default: 5)"
            echo "  --download        Test downloading a sample file"
            echo "  --sample NAME     Sample file name (default: sample_1000)"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# If no tests specified, run all tests
if [ "$API_KEY_TEST" = false ] && [ "$VALIDATE_TEST" = false ] && [ "$BATCH_TEST" = false ] && [ "$DOWNLOAD_TEST" = false ]; then
    # Run all tests
    echo -e "\nRunning all tests..."
    python test_scripts/test_pesalink_api.py $VERBOSE
else
    # Run individual tests
    if [ "$API_KEY_TEST" = true ]; then
        echo -e "\nTesting API key retrieval..."
        python test_scripts/test_pesalink_api.py --key $VERBOSE
    fi

    if [ "$VALIDATE_TEST" = true ]; then
        echo -e "\nTesting account validation..."
        python test_scripts/test_pesalink_api.py --validate --account "$ACCOUNT_NUMBER" --bank "$BANK_CODE" $VERBOSE
    fi

    if [ "$BATCH_TEST" = true ]; then
        echo -e "\nTesting batch validation with $BATCH_SIZE accounts..."
        python test_scripts/test_pesalink_api.py --batch --batch-size "$BATCH_SIZE" $VERBOSE
    fi

    if [ "$DOWNLOAD_TEST" = true ]; then
        echo -e "\nTesting sample file download..."
        python test_scripts/test_pesalink_api.py --download --sample "$SAMPLE_NAME" $VERBOSE
    fi
fi

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\nAPI tests completed successfully! 🎉"
else
    echo -e "\nAPI tests failed with exit code $EXIT_CODE ❌"
fi

exit $EXIT_CODE