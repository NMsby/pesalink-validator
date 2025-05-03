"""
Test script for the PesaLink API integration.
This script demonstrates how to use the PesaLink API client to validate accounts.
"""
import os
import sys
import logging
import argparse
import json
from datetime import datetime

# Add the parent directory to the path to import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.pesalink_client import PesaLinkClient
from app.models.account import Account
from app.models.validation_result import ValidationStatus
from app.utils.logger import setup_logger


def test_api_key():
    """
    Test fetching the API key.

    Returns:
        str: API key
    """
    print("Testing API key retrieval...")
    client = PesaLinkClient()
    api_key = client._fetch_api_key()

    # Mask the API key for display
    if api_key:
        masked_key = api_key[:5] + '*' * (len(api_key) - 10) + api_key[-5:]
        print(f"✅ Successfully retrieved API key: {masked_key}")
    else:
        print("❌ Failed to retrieve API key")

    return api_key


def test_account_validation(account_number, bank_code):
    """
    Test validating a single account.

    Args:
        account_number (str): Account number to validate
        bank_code (str): Bank code

    Returns:
        ValidationResult: Validation result
    """
    print(f"\nTesting account validation for account {account_number} at bank {bank_code}...")
    client = PesaLinkClient()

    # Create an account object
    account = Account(
        account_number=account_number,
        bank_code=bank_code,
        reference_id=f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        amount=1000.0,
        currency="KES"
    )

    # Validate the account
    result = client.validate_account(account)

    print("\nValidation Result:")
    print(f"Status: {result.status}")

    if result.status == ValidationStatus.VALID:
        print(f"✅ Account is valid")
        print(f"Account Holder Name: {result.validated_name}")
        print(f"Account Status: {result.account_status}")
        print(f"Bank Name: {result.bank_name}")
    else:
        print(f"❌ Account validation failed")
        print(f"Error Code: {result.error_code}")
        print(f"Error Message: {result.error_message}")

    return result


def test_batch_validation(accounts):
    """
    Test validating a batch of accounts.

    Args:
        accounts (list): List of Account objects

    Returns:
        list: List of ValidationResult objects
    """
    print(f"\nTesting batch validation for {len(accounts)} accounts...")
    client = PesaLinkClient()

    # Validate the accounts
    results = client.validate_accounts_batch(accounts)

    # Analyze results
    valid_count = sum(1 for r in results if r.status == ValidationStatus.VALID)
    invalid_count = sum(1 for r in results if r.status == ValidationStatus.INVALID)
    error_count = sum(1 for r in results if r.status == ValidationStatus.ERROR)

    print("\nBatch Validation Results:")
    print(f"Total Accounts: {len(results)}")
    print(f"Valid Accounts: {valid_count}")
    print(f"Invalid Accounts: {invalid_count}")
    print(f"Error Accounts: {error_count}")

    # Display details for each result
    for i, result in enumerate(results):
        account = result.account
        print(f"\nAccount {i + 1}: {account.account_number} (Bank: {account.bank_code})")
        print(f"Status: {result.status}")
        if result.status == ValidationStatus.VALID:
            print(f"Account Holder: {result.validated_name}")
        else:
            print(f"Error: {result.error_message}")

    return results


def test_download_sample(sample_name="sample_1000", output_dir="sample_data"):
    """
    Test downloading a sample file.

    Args:
        sample_name (str): Sample file name
        output_dir (str): Output directory

    Returns:
        str: Path to downloaded file
    """
    print(f"\nTesting sample file download for {sample_name}...")
    client = PesaLinkClient()

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Download the file
    file_path = client.download_sample_accounts(sample_name, output_dir)

    if file_path:
        print(f"✅ Successfully downloaded sample file to: {file_path}")

        # Display file information
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size} bytes")

        # Count lines in the file
        with open(file_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)

        print(f"Total lines: {line_count} (including header)")
    else:
        print("❌ Failed to download sample file")

    return file_path


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the PesaLink API integration")
    parser.add_argument("--key", action="store_true", help="Test fetching the API key")
    parser.add_argument("--validate", action="store_true", help="Test account validation")
    parser.add_argument("--account", default="123456789", help="Account number to validate")
    parser.add_argument("--bank", default="ABC", help="Bank code for validation")
    parser.add_argument("--batch", action="store_true", help="Test batch validation")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of accounts in the test batch")
    parser.add_argument("--download", action="store_true", help="Test downloading a sample file")
    parser.add_argument("--sample", default="sample_1000", help="Sample file name to download")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(log_level)

    # If no specific tests are selected, run all tests
    run_all = not (args.key or args.validate or args.batch or args.download)

    print("PesaLink API Integration Test")
    print("============================")

    try:
        # Test fetching the API key
        if args.key or run_all:
            api_key = test_api_key()

        # Test validating a single account
        if args.validate or run_all:
            test_account_validation(args.account, args.bank)

        # Test batch validation
        if args.batch or run_all:
            # Create test accounts
            accounts = []
            for i in range(args.batch_size):
                account = Account(
                    account_number=f"{args.account}{i}",
                    bank_code=args.bank,
                    reference_id=f"BATCH-{i + 1}",
                    amount=1000.0 * (i + 1),
                    currency="KES"
                )
                accounts.append(account)

            test_batch_validation(accounts)

        # Test downloading a sample file
        if args.download or run_all:
            test_download_sample(args.sample)

        print("\nTest completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
