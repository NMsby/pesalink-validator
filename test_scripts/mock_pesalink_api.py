"""
Mock PesaLink API for testing the Bulk Account Validator without a real API.
This script implements a Flask server that simulates the PesaLink Account Validation API.
"""
import os
import json
import random
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/mock_api.log')
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Define mock data
VALID_ACCOUNTS = {
    "01": {
        "1234567890": {"account_holder_name": "John Doe", "status": "ACTIVE", "bank_name": "ABC Bank"},
        "5555555555": {"account_holder_name": "Alice Johnson", "status": "ACTIVE", "bank_name": "ABC Bank"},
        "3333444455": {"account_holder_name": "Eve Davis", "status": "ACTIVE", "bank_name": "ABC Bank"}
    },
    "02": {
        "9876543210": {"account_holder_name": "Jane Smith", "status": "ACTIVE", "bank_name": "XYZ Bank"},
        "7777666655": {"account_holder_name": "David Miller", "status": "ACTIVE", "bank_name": "XYZ Bank"},
        "5551212121": {"account_holder_name": "Missing Name", "status": "ACTIVE", "bank_name": "XYZ Bank"}
    },
    "03": {
        "1111222233": {"account_holder_name": "Bob Williams", "status": "ACTIVE", "bank_name": "LMN Bank"},
        "2468135790": {"account_holder_name": "Grace Taylor", "status": "INACTIVE", "bank_name": "LMN Bank"}
    },
    "04": {
        "9999888877": {"account_holder_name": "Carol Brown", "status": "ACTIVE", "bank_name": "PQR Bank"},
        "1357924680": {"account_holder_name": "Henry Anderson", "status": "CLOSED", "bank_name": "PQR Bank"}
    },
    "05": {
        "8765432109": {"account_holder_name": "Frank Wilson", "status": "BLOCKED", "bank_name": "STU Bank"}
    }
}

VALID_BANK_CODES = ["01", "02", "03", "04", "05"]

# Define error codes
ERROR_CODES = {
    "ACCOUNT_NOT_FOUND": {"code": "AC01", "message": "Account does not exist"},
    "ACCOUNT_CLOSED": {"code": "AC04", "message": "Account is closed"},
    "ACCOUNT_BLOCKED": {"code": "AC06", "message": "Account is blocked"},
    "ACCOUNT_INACTIVE": {"code": "AC07", "message": "Account is inactive"},
    "INVALID_FORMAT": {"code": "RJCT", "message": "Invalid format"},
    "INVALID_BANK": {"code": "AM04", "message": "Invalid bank code"}
}

# Mock API key
MOCK_API_KEY = "609dab841280674f1a780272f59e9e4e"


# Define API endpoints
@app.route('/api/key', methods=['GET'])
def get_api_key():
    """
    Mock endpoint for getting an API key.

    Returns:
        JSON response with an API key
    """
    logger.info("API key request received")

    return jsonify({
        "apiKey": MOCK_API_KEY
    })


@app.route('/api/validate', methods=['POST'])
def validate_account():
    """
    Mock endpoint for validating an account.

    Returns:
        JSON response with a validation result
    """
    # Check if request has data
    if not request.is_json:
        logger.warning("Invalid request format: not JSON")
        return jsonify({
            "status": "Invalid",
            "errorCode": "RJCT",
            "errorDescription": "Invalid request format"
        }), 400

    # Check authorization
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer ') or auth_header[7:] != MOCK_API_KEY:
        logger.warning(f"Invalid API key: {auth_header}")
        return jsonify({
            "status": "Invalid",
            "errorCode": "AUTH",
            "errorDescription": "Invalid API key"
        }), 401

    data = request.json
    logger.info(f"Account validation request: {json.dumps(data)}")

    # Extract account details
    account_number = data.get('accountNumber')
    bank_code = data.get('bankCode')

    # Validate required fields
    if not account_number or not bank_code:
        logger.warning("Missing required fields")
        return jsonify({
            "status": "Invalid",
            "errorCode": "RJCT",
            "errorDescription": "Missing required fields"
        }), 400

    # Add artificial delay to simulate network latency (0.1-0.5 seconds)
    import time
    time.sleep(random.uniform(0.1, 0.5))

    # Validate bank code
    if bank_code not in VALID_BANK_CODES:
        logger.info(f"Invalid bank code: {bank_code}")
        return jsonify({
            "accountNumber": account_number,
            "bankCode": bank_code,
            "status": "Invalid",
            "errorCode": ERROR_CODES["INVALID_BANK"]["code"],
            "errorDescription": ERROR_CODES["INVALID_BANK"]["message"]
        })

    # Check if an account has an invalid format (contains non-numeric characters)
    if not account_number.isdigit():
        logger.info(f"Invalid account format: {account_number}")
        return jsonify({
            "accountNumber": account_number,
            "bankCode": bank_code,
            "status": "Invalid",
            "errorCode": ERROR_CODES["INVALID_FORMAT"]["code"],
            "errorDescription": ERROR_CODES["INVALID_FORMAT"]["message"]
        })

    # Check if an account is too short or too long
    if len(account_number) < 6 or len(account_number) > 20:
        logger.info(f"Invalid account length: {len(account_number)}")
        return jsonify({
            "accountNumber": account_number,
            "bankCode": bank_code,
            "status": "Invalid",
            "errorCode": ERROR_CODES["INVALID_FORMAT"]["code"],
            "errorDescription": "Account number length is invalid"
        })

    # Check if an account exists
    if bank_code in VALID_ACCOUNTS and account_number in VALID_ACCOUNTS[bank_code]:
        # Get account details
        account_info = VALID_ACCOUNTS[bank_code][account_number]

        # Check account status
        if account_info["status"] == "CLOSED":
            logger.info(f"Account is closed: {account_number}")
            return jsonify({
                "accountNumber": account_number,
                "bankCode": bank_code,
                "status": "Invalid",
                "errorCode": ERROR_CODES["ACCOUNT_CLOSED"]["code"],
                "errorDescription": ERROR_CODES["ACCOUNT_CLOSED"]["message"]
            })
        elif account_info["status"] == "INACTIVE":
            logger.info(f"Account is inactive: {account_number}")
            return jsonify({
                "accountNumber": account_number,
                "bankCode": bank_code,
                "status": "Invalid",
                "errorCode": ERROR_CODES["ACCOUNT_INACTIVE"]["code"],
                "errorDescription": ERROR_CODES["ACCOUNT_INACTIVE"]["message"]
            })
        elif account_info["status"] == "BLOCKED":
            logger.info(f"Account is blocked: {account_number}")
            return jsonify({
                "accountNumber": account_number,
                "bankCode": bank_code,
                "status": "Invalid",
                "errorCode": ERROR_CODES["ACCOUNT_BLOCKED"]["code"],
                "errorDescription": ERROR_CODES["ACCOUNT_BLOCKED"]["message"]
            })
        else:
            # Account is valid and active
            logger.info(f"Valid account: {account_number}")
            return jsonify({
                "accountNumber": account_number,
                "bankCode": bank_code,
                "status": "Valid",
                "accountHolderName": account_info["account_holder_name"],
                "bankName": account_info["bank_name"],
                "currency": "KES"
            })
    else:
        # If we don't have the account in our test data, but it looks valid (right format, etc.)
        # we'll randomly decide if it's valid or not (70% chance of being valid)
        if random.random() < 0.7:
            # Generate a random name
            first_names = ["John", "Mary", "James", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William",
                           "Elizabeth"]
            last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore",
                          "Taylor"]
            random_name = f"{random.choice(first_names)} {random.choice(last_names)}"

            # Get bank name based on bank code
            bank_names = {
                "01": "ABC Bank",
                "02": "XYZ Bank",
                "03": "LMN Bank",
                "04": "PQR Bank",
                "05": "STU Bank"
            }
            bank_name = bank_names.get(bank_code, "Unknown Bank")

            logger.info(f"Randomly generated valid account: {account_number}")
            return jsonify({
                "accountNumber": account_number,
                "bankCode": bank_code,
                "status": "Valid",
                "accountHolderName": random_name,
                "bankName": bank_name,
                "currency": "KES"
            })
        else:
            # Account not found
            logger.info(f"Account not found: {account_number}")
            return jsonify({
                "accountNumber": account_number,
                "bankCode": bank_code,
                "status": "Invalid",
                "errorCode": ERROR_CODES["ACCOUNT_NOT_FOUND"]["code"],
                "errorDescription": ERROR_CODES["ACCOUNT_NOT_FOUND"]["message"]
            })


@app.route('/download/<file_name>', methods=['GET'])
def download_sample_file(file_name):
    """
    Mock endpoint for downloading sample account data.

    Args:
        file_name (str): Name of the file to download

    Returns:
        CSV file with sample account data
    """
    logger.info(f"Download request received for: {file_name}")

    # Check authorization
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer ') or auth_header[7:] != MOCK_API_KEY:
        logger.warning(f"Invalid API key: {auth_header}")
        return jsonify({
            "error": "Invalid API key"
        }), 401

    # Sanitize file name
    file_name = file_name.replace('..', '').replace('/', '').replace('\\', '')

    # Generate sample data if it doesn't exist
    sample_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data")
    os.makedirs(sample_dir, exist_ok=True)

    # Determine the number of accounts
    try:
        num_accounts = int(file_name.split('_')[1]) if '_' in file_name else 100
    except (ValueError, IndexError):
        num_accounts = 100

    output_file = os.path.join(sample_dir, f"{file_name}_accounts.csv")

    # Generate sample data if a file doesn't exist or is empty
    if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
        logger.info(f"Generating sample data file: {output_file} with {num_accounts} accounts")
        generate_sample_file(output_file, num_accounts)

    # Return the file
    return send_file(output_file, as_attachment=True, download_name=f"{file_name}_accounts.csv")


def generate_sample_file(output_file, num_accounts):
    """
    Generate a sample CSV file with random accounts.

    Args:
        output_file (str): Path to the output file
        num_accounts (int): Number of accounts to generate
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Define valid account patterns
    valid_accounts = []
    for bank_code in VALID_BANK_CODES:
        for account_number in VALID_ACCOUNTS.get(bank_code, {}):
            valid_accounts.append((account_number, bank_code))

    # Generate random accounts
    with open(output_file, 'w', newline='') as f:
        f.write("Account Number,Bank Code\n")

        # Add all known valid accounts first (if there are enough)
        for i, (account, bank) in enumerate(valid_accounts):
            if i >= num_accounts:
                break
            f.write(f"{account},{bank}\n")

        # Generate random accounts for the rest
        for i in range(len(valid_accounts), num_accounts):
            # 80% chance of valid account format
            if random.random() < 0.8:
                account_number = ''.join(random.choices("0123456789", k=10))
                bank_code = random.choice(VALID_BANK_CODES)
            else:
                # Generate an invalid account
                invalid_types = [
                    # Too short
                    lambda: ''.join(random.choices("0123456789", k=random.randint(2, 5))),
                    # Too long
                    lambda: ''.join(random.choices("0123456789", k=random.randint(21, 30))),
                    # Contains non-digits
                    lambda: ''.join(random.choices("0123456789ABCDEFabcdef", k=10)),
                    # Invalid bank code
                    lambda: (''.join(random.choices("0123456789", k=10)),
                             str(random.randint(6, 99)).zfill(2)),
                ]

                invalid_generator = random.choice(invalid_types)
                if callable(invalid_generator):
                    result = invalid_generator()
                    if isinstance(result, tuple):
                        account_number, bank_code = result
                    else:
                        account_number = result
                        bank_code = random.choice(VALID_BANK_CODES)

            f.write(f"{account_number},{bank_code}\n")


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    print(f"Starting mock PesaLink API server on port {port}...")
    print(f"API Key: {MOCK_API_KEY}")
    print("Endpoints:")
    print(f"- GET http://localhost:{port}/api/key")
    print(f"- POST http://localhost:{port}/api/validate")
    print(f"- GET http://localhost:{port}/download/<file_name>")
    print("Press Ctrl+C to stop the server")

    app.run(host='0.0.0.0', port=port, debug=True)
