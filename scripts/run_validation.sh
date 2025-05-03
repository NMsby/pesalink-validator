#!/bin/bash

# Script to run the PesaLink bulk account validation

# Set default values
INPUT_FILE="sample_data/sample_1000_accounts.csv"
OUTPUT_DIR="output"
BATCH_SIZE=100
WORKERS=10
PARALLEL=false
NOTIFY=false
VERBOSE=false

# Display help message
function show_help {
    echo "PesaLink Bulk Account Validator Runner"
    echo "====================================="
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -i, --input FILE      Input CSV file (default: $INPUT_FILE)"
    echo "  -o, --output DIR      Output directory (default: $OUTPUT_DIR)"
    echo "  -b, --batch-size N    Maximum batch size (default: $BATCH_SIZE)"
    echo "  -w, --workers N       Number of worker threads (default: $WORKERS)"
    echo "  -p, --parallel        Enable parallel processing"
    echo "  -n, --notify          Send email notification when complete"
    echo "  -v, --verbose         Enable verbose logging"
    echo "  -h, --help            Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --input sample_data/sample_1000_accounts.csv --output results --parallel"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            INPUT_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -b|--batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        -w|--workers)
            WORKERS="$2"
            shift 2
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -n|--notify)
            NOTIFY=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Prepare command
CMD="python scripts/validate_pesalink_accounts.py --input $INPUT_FILE --output $OUTPUT_DIR --batch-size $BATCH_SIZE --workers $WORKERS"

if [ "$PARALLEL" = true ]; then
    CMD="$CMD --parallel"
fi

if [ "$NOTIFY" = true ]; then
    CMD="$CMD --notify"
fi

if [ "$VERBOSE" = true ]; then
    CMD="$CMD --verbose"
fi

# Print configuration
echo "PesaLink Bulk Account Validator"
echo "=============================="
echo ""
echo "Configuration:"
echo "  Input File:       $INPUT_FILE"
echo "  Output Directory: $OUTPUT_DIR"
echo "  Batch Size:       $BATCH_SIZE"
echo "  Workers:          $WORKERS"
echo "  Parallel:         $PARALLEL"
echo "  Notify:           $NOTIFY"
echo "  Verbose:          $VERBOSE"
echo ""
echo "Starting validation..."
echo ""

# Run the validation script
eval "$CMD"

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Validation failed with exit code $EXIT_CODE"
    exit $EXIT_CODE
fi

echo ""
echo "Validation completed successfully!"