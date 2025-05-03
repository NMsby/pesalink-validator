"""
Utility for handling PesaLink sample data format.
This module converts between PesaLink's data format and our internal Account model.
"""
import os
import csv
import logging
from typing import List, Dict, Optional, Any

from app.models.account import Account
from app.utils.logger import LoggerMixin

logger = logging.getLogger(__name__)


class PesaLinkDataHandler(LoggerMixin):
    """Handles conversion between PesaLink data format and internal models."""

    @staticmethod
    def convert_to_accounts(csv_path: str, include_reference_id: bool = True) -> List[Account]:
        """
        Convert PesaLink CSV data to a list of Account objects.

        Args:
            csv_path (str): Path to the CSV file
            include_reference_id (bool): Whether to include a reference ID

        Returns:
            List[Account]: List of Account objects
        """
        accounts = []

        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for i, row in enumerate(reader, start=1):
                    try:
                        # Extract account data
                        account_number = row.get('Account Number', '')
                        bank_code = row.get('Bank Code', '')

                        # Skip rows with missing required fields
                        if not account_number or not bank_code:
                            logger.warning(f"Row {i}: Missing required fields. Skipping.")
                            continue

                        # Create reference ID if needed
                        reference_id = f"REF-{i}" if include_reference_id else ""

                        # Create an Account object
                        account = Account(
                            account_number=account_number,
                            bank_code=bank_code,
                            reference_id=reference_id,
                            # Default values for other fields
                            amount=0.0,
                            currency="KES"
                        )

                        accounts.append(account)

                    except Exception as e:
                        logger.warning(f"Error processing row {i}: {str(e)}. Skipping.")

            logger.info(f"Converted {len(accounts)} accounts from {csv_path}")
            return accounts

        except Exception as e:
            logger.error(f"Error reading CSV file {csv_path}: {str(e)}")
            raise

    @staticmethod
    def convert_to_csv(accounts: List[Account], csv_path: str) -> str:
        """
        Convert a list of Account objects to PesaLink CSV format.

        Args:
            accounts (List[Account]): List of Account objects
            csv_path (str): Path to the output CSV file

        Returns:
            str: Path to the created CSV file
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Account Number', 'Bank Code']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                for account in accounts:
                    writer.writerow({
                        'Account Number': account.account_number,
                        'Bank Code': account.bank_code
                    })

            logger.info(f"Converted {len(accounts)} accounts to {csv_path}")
            return csv_path

        except Exception as e:
            logger.error(f"Error writing CSV file {csv_path}: {str(e)}")
            raise

    @staticmethod
    def merge_validation_results(accounts: List[Account], results: List[Dict], csv_path: str) -> str:
        """
        Merge account information with validation results and save to CSV.

        Args:
            accounts (List[Account]): List of Account objects
            results (List[Dict]): List of validation results
            csv_path (str): Path to the output CSV file

        Returns:
            str: Path to the created CSV file
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)

            # Create a lookup dictionary for validation results
            result_dict = {}
            for r in results:
                # Handle both dictionary and ValidationResult object formats
                if isinstance(r, dict):
                    account_number = r.get('account_number') or r.get('accountNumber')
                    bank_code = r.get('bank_code') or r.get('bankCode')
                    if account_number and bank_code:
                        key = f"{account_number}_{bank_code}"
                        result_dict[key] = r
                else:
                    # Assume it's a ValidationResult object
                    key = f"{r.account.account_number}_{r.account.bank_code}"
                    result_dict[key] = r.to_dict() if hasattr(r, 'to_dict') else r

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Account Number',
                    'Bank Code',
                    'Validation Status',
                    'Account Holder Name',
                    'Bank Name',
                    'Currency',
                    'Error Message'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                for account in accounts:
                    # Look up a validation result
                    key = f"{account.account_number}_{account.bank_code}"
                    result = result_dict.get(key, {})

                    # Extract validation data
                    if isinstance(result, dict):
                        status = result.get('status') or result.get('validation_status', 'Not Validated')
                        account_holder_name = result.get('validated_name') or result.get('accountHolderName', '')
                        bank_name = result.get('bank_name') or result.get('bankName', '')
                        currency = result.get('currency', 'KES')
                        error_message = result.get('error_message') or result.get('errorMessage', '')
                    else:
                        # Fallback for an unexpected result type
                        status = 'Unknown'
                        account_holder_name = ''
                        bank_name = ''
                        currency = 'KES'
                        error_message = 'Unexpected result format'

                    # Create row
                    row = {
                        'Account Number': account.account_number,
                        'Bank Code': account.bank_code,
                        'Validation Status': status,
                        'Account Holder Name': account_holder_name,
                        'Bank Name': bank_name,
                        'Currency': currency
                    }

                    # Add an error message if any
                    if status != 'Valid':
                        row['Error Message'] = error_message

                    writer.writerow(row)

            logger.info(f"Merged validation results for {len(accounts)} accounts to {csv_path}")
            return csv_path

        except Exception as e:
            logger.error(f"Error merging validation results to {csv_path}: {str(e)}")
            raise

    @staticmethod
    def convert_from_internal_format(input_file: str, output_file: str) -> str:
        """
        Convert from internal CSV format to PesaLink CSV format.

        Args:
            input_file (str): Path to the input CSV file in internal format
            output_file (str): Path to the output CSV file in PesaLink format

        Returns:
            str: Path to the created CSV file
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Read an input file
            accounts = []
            with open(input_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)

                for row in reader:
                    # Extract required fields
                    account_number = row.get('account_number', '')
                    bank_code = row.get('bank_code', '')

                    if account_number and bank_code:
                        accounts.append(Account(
                            account_number=account_number,
                            bank_code=bank_code,
                            reference_id=""
                        ))

            # Write an output file
            return PesaLinkDataHandler.convert_to_csv(accounts, output_file)

        except Exception as e:
            logger.error(f"Error converting from internal format: {str(e)}")
            raise

    @staticmethod
    def split_batch(input_file: str, batch_size: int, output_dir: str) -> List[str]:
        """
        Split a large CSV file into smaller batches.

        Args:
            input_file (str): Path to the input CSV file
            batch_size (int): Maximum number of accounts per batch
            output_dir (str): Directory for output files

        Returns:
            List[str]: List of paths to the created batch files
        """
        try:
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Read an input file
            accounts = PesaLinkDataHandler.convert_to_accounts(input_file, include_reference_id=False)

            if not accounts:
                logger.warning(f"No accounts found in {input_file}")
                return []

            # Split into batches
            batch_files = []
            for i in range(0, len(accounts), batch_size):
                batch = accounts[i:i + batch_size]
                batch_file = os.path.join(output_dir, f"batch_{i // batch_size + 1}.csv")
                PesaLinkDataHandler.convert_to_csv(batch, batch_file)
                batch_files.append(batch_file)

            logger.info(f"Split {len(accounts)} accounts into {len(batch_files)} batches")
            return batch_files

        except Exception as e:
            logger.error(f"Error splitting batch: {str(e)}")
            raise
