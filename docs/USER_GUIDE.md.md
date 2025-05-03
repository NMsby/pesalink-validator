# PesaLink Bulk Account Validator - User Guide

This guide provides instructions for using the PesaLink Bulk Account Validator to validate bank accounts in bulk before processing transactions.

## Overview

The PesaLink Bulk Account Validator helps you prevent AC-01 errors (invalid account errors) by validating account details before initiating transactions. It accepts files with account information, validates each account against the PesaLink API, and generates comprehensive reports.

## Installation

### Prerequisites

- Python 3.8+
- Internet connection to access the PesaLink API

### Method 1: Direct Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pesalink-validator.git
   cd pesalink-validator
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up configuration:
   ```
   cp .env.example .env
   # Edit .env file with your settings
   ```

### Method 2: Docker Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pesalink-validator.git
   cd pesalink-validator
   ```

2. Configure environment variables:
   ```
   cp .env.example .env
   # Edit .env file with your settings
   ```

3. Build and run with Docker Compose:
   ```
   docker-compose build
   docker-compose up
   ```

## Basic Usage

### Command Line Interface

The validator can be run from the command line with various options:

```
python -m app.main --input INPUT_FILE --output OUTPUT_DIR [options]
```

#### Required Parameters:

- `--input`, `-i`: Path to the input file (CSV, JSON, or XML)

#### Optional Parameters:

- `--output`, `-o`: Output directory for reports (default: `output`)
- `--format`, `-f`: Output format for reports (`csv`, `json`, or `xml`, default: `csv`)
- `--parallel`, `-p`: Enable parallel processing
- `--batch-size`, `-b`: Maximum batch size for processing (default: 1000)
- `--workers`, `-w`: Number of worker threads for parallel processing (default: 10)
- `--notify`, `-n`: Send email notification when complete
- `--pesalink`: Treat input as PesaLink format CSV
- `--verbose`, `-v`: Enable verbose logging

### Using the Shell Script

For convenience, a shell script is provided:

```
./scripts/run_validation.sh --input INPUT_FILE --output OUTPUT_DIR [options]
```

This script accepts the same parameters as the command line interface.

## Input File Formats

The validator supports multiple input file formats:

### CSV Format

```csv
account_number,bank_code
1234567890,01
9876543210,02
```

### PesaLink CSV Format

```csv
Account Number,Bank Code
1234567890,01
9876543210,02
```

### JSON Format

```json
{
  "accounts": [
    {
      "account_number": "1234567890",
      "bank_code": "01"
    },
    {
      "account_number": "9876543210",
      "bank_code": "02"
    }
  ]
}
```

### XML Format

```xml
<accounts>
  <account>
    <account_number>1234567890</account_number>
    <bank_code>01</bank_code>
  </account>
  <account>
    <account_number>9876543210</account_number>
    <bank_code>02</bank_code>
  </account>
</accounts>
```

## Output Reports

The validator generates several reports:

1. **Summary Report**: Overview of validation results
2. **Valid Accounts Report**: List of accounts that passed validation
3. **Invalid Accounts Report**: List of accounts that failed validation with reason codes
4. **Error Report**: Accounts that encountered processing errors
5. **Statistics Report**: Detailed statistics about the validation process

### Sample Summary Report (CSV)

```csv
category,count,percentage
Total Accounts,1000,100.0
Valid Accounts,850,85.0
Invalid Accounts,120,12.0
Error Accounts,30,3.0
Error Code: ACCOUNT_NOT_FOUND,80,8.0
Error Code: INVALID_FORMAT,40,4.0
```

### PesaLink Format Reports

The validator also generates reports in PesaLink format that can be used for further processing:

- `pesalink_valid_[timestamp].csv`: Valid accounts in PesaLink format
- `pesalink_invalid_[timestamp].csv`: Invalid accounts in PesaLink format

## Use Cases

### 1. Pre-validation of Payment File

Before submitting a payment file to the bank, validate all accounts:

```
python -m app.main --input payments.csv --output validation_results --format csv --parallel
```

### 2. Incremental Validation

To validate a file incrementally (useful for very large files):

```
# Split the file
python -c "
import sys
sys.path.append('.')
from app.utils.pesalink_data_handler import PesaLinkDataHandler
PesaLinkDataHandler.split_batch('large_file.csv', 1000, 'batches')
"

# Validate each batch
for batch in batches/*.csv; do
  python -m app.main --input $batch --output validation_results --parallel
done
```

### 3. Integration with Other Systems

The validator can be easily integrated with other systems by using the Docker container:

```
docker run -v /path/to/data:/app/data -v /path/to/output:/app/output pesalink-validator --input /app/data/accounts.csv --output /app/output
```

## Troubleshooting

### Common Issues

1. **API Connection Issues**
   - Check your internet connection
   - Verify that the API base URL is correct in your `.env` file
   - Test the API connection: `python test_scripts/test_pesalink_api.py --key`

2. **File Format Issues**
   - Verify that your input file is in the correct format
   - Check for missing or invalid headers
   - Look for encoding issues (use UTF-8 encoding)

3. **Performance Issues**
   - For large files, use parallel processing: `--parallel`
   - Increase the batch size: `--batch-size 2000`
   - Increase worker threads for parallel processing: `--workers 20`

### Checking Logs

Logs are stored in the `logs` directory. Check the following files for troubleshooting:

- `validator.log`: Main application log
- `api.log`: API communication log
- `error.log`: Detailed error log

### Getting Help

If you encounter issues that you cannot resolve, please:

1. Run the diagnostic script: `./test_scripts/run_tests.sh`
2. Collect the logs from the `logs` directory
3. Open an issue on the project's GitHub repository with the logs and a description of the issue

## Advanced Features

### Email Notifications

The validator can send email notifications when validation is complete. To enable this feature:

1. Configure email settings in your `.env` file:
   ```
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587
   SMTP_USERNAME=your_username
   SMTP_PASSWORD=your_password
   FROM_EMAIL=noreply@example.com
   NOTIFICATION_EMAILS=["admin@example.com", "team@example.com"]
   ```

2. Use the `--notify` flag when running the validator:
   ```
   python -m app.main --input accounts.csv --output results --notify
   ```

### Performance Tuning

For optimal performance, consider the following settings:

1. **Batch Size**: Adjust based on available memory
   - For systems with limited memory: `--batch-size 500`
   - For systems with ample memory: `--batch-size 2000`

2. **Worker Threads**: Adjust based on CPU cores
   - For 4-core systems: `--workers 8`
   - For 8-core systems: `--workers 16`
   - For 16-core systems: `--workers 32`

3. **Parallel Processing**: Always enable for large files
   - Use the `--parallel` flag

### Load Testing

To test the system's performance under different loads:

```
python test_scripts/load_test.py --generate --accounts 10000 --iterations 3
```

This will generate test data and run various benchmarks to find optimal settings for your environment.

## Best Practices

1. **Input Data Quality**
   - Ensure account numbers and bank codes follow the correct format
   - Remove duplicates and obviously invalid entries before validation
   - Use consistent formatting for account numbers

2. **Batch Processing**
   - Split very large files (>100,000 accounts) into multiple batches
   - Process batches during off-peak hours to minimize API load
   - Monitor API rate limits and adjust batch timing accordingly

3. **Output Management**
   - Archive validation results for audit purposes
   - Review error patterns to identify systemic issues
   - Implement periodic data quality checks based on validation results

4. **Security Considerations**
   - Regularly rotate API keys
   - Store sensitive data (like `.env` files) securely
   - Use encryption for storing validation results
   - Restrict access to input and output files

## Next Steps

After validating accounts, you can:

1. **Process valid accounts**: Use the `valid_accounts_*.csv` file for payment processing
2. **Review invalid accounts**: Investigate and correct issues with accounts in the `invalid_accounts_*.csv` file
3. **Analyze patterns**: Review the statistics report to identify common error patterns and improve data quality

## Support and Feedback

For support, questions, or feedback, please contact:
- Email: support@example.com
- GitHub Issues: https://github.com/yourusername/pesalink-validator/issues
