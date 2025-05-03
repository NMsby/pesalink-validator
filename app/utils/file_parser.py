"""
File parsing utilities for handling different input file formats.
"""
import os
import csv
import json
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from app.models.account import Account
from app.models.batch import Batch
from app.utils.logger import LoggerMixin

logger = logging.getLogger(__name__)


class FileParser(LoggerMixin):
    """Parses input files in various formats (CSV, JSON, XML)."""

    def parse(self, file_path: str) -> List[Account]:
        """
        Parse an input file and extract account information.

        Args:
            file_path (str): Path to the input file

        Returns:
            List[Account]: List of Account objects

        Raises:
            ValueError: If the file format is not supported
            FileNotFoundError: If the file does not exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.csv':
            return self._parse_csv(file_path)
        elif ext == '.json':
            return self._parse_json(file_path)
        elif ext == '.xml':
            return self._parse_xml(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def create_batch(self, file_path: str) -> Batch:
        """
        Create a batch from an input file.

        Args:
            file_path (str): Path to the input file

        Returns:
            Batch: Batch object containing accounts
        """
        accounts = self.parse(file_path)

        # Extract metadata from the file
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # Create batch with metadata
        batch = Batch(
            accounts=accounts,
            metadata={
                "source_file": file_name,
                "file_size": file_size,
                "account_count": len(accounts)
            }
        )

        return batch

    def _parse_csv(self, file_path: str) -> List[Account]:
        """
        Parse a CSV file to extract account information.

        Args:
            file_path (str): Path to the CSV file

        Returns:
            List[Account]: List of Account objects
        """
        accounts = []

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Check if needed columns are present
                required_columns = ['account_number', 'bank_code']
                # Attempt to match column names in a case-insensitive way
                fieldnames_lower = [field.lower() for field in reader.fieldnames]
                column_mapping = {}
                for req_col in required_columns:
                    for i, field in enumerate(fieldnames_lower):
                        if req_col == field or req_col.replace('_', ' ') == field:
                            column_mapping[req_col] = reader.fieldnames[i]
                            break

                missing_columns = [col for col in required_columns if col not in column_mapping]
                if missing_columns:
                    # Special handling for PesaLink format
                    if 'account number' in [f.lower() for f in reader.fieldnames] and 'bank code' in [f.lower() for f in
                                                                                                      reader.fieldnames]:
                        self.logger.info("Detected PesaLink format CSV")
                        return self._parse_pesalink_csv(file_path)
                    else:
                        raise ValueError(f"Missing required columns in CSV: {', '.join(missing_columns)}")

                # Process each row
                for i, row in enumerate(reader, start=2):  # Start at line 2 (after header)
                    try:
                        # Normalize column names (strip whitespace, convert to lowercase)
                        normalized_row = {}
                        for key, value in row.items():
                            normalized_key = key.strip().lower()
                            normalized_row[normalized_key] = value

                        # Map columns to required fields
                        account_data = {}
                        for req_col, csv_col in column_mapping.items():
                            account_data[req_col] = row.get(csv_col, '')

                        # Add additional fields if present
                        for field in ['reference_id', 'amount', 'currency', 'account_name', 'phone_number',
                                      'transaction_type']:
                            for key, value in normalized_row.items():
                                if field == key or field.replace('_', ' ') == key:
                                    account_data[field] = value
                                    break

                        # Create a reference ID if not provided
                        if not account_data.get('reference_id'):
                            account_data['reference_id'] = f"REF-{i}"

                        account = Account.from_dict(account_data)
                        accounts.append(account)
                    except Exception as e:
                        self.logger.warning(f"Error parsing row {i}: {str(e)}. Skipping row.")
                        continue

        except Exception as e:
            self.logger.error(f"Error parsing CSV file: {str(e)}")
            raise

        self.logger.info(f"Successfully parsed {len(accounts)} accounts from CSV file: {file_path}")
        return accounts

    def _parse_pesalink_csv(self, file_path: str) -> List[Account]:
        """
        Parse a PesaLink format CSV file.

        Args:
            file_path (str): Path to the CSV file

        Returns:
            List[Account]: List of Account objects
        """
        accounts = []

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for i, row in enumerate(reader, start=2):
                    try:
                        # Map PesaLink column names to our model
                        account_data = {
                            'account_number': row.get('Account Number', ''),
                            'bank_code': row.get('Bank Code', ''),
                            'reference_id': f"PL-{i}",
                            'currency': 'KES'
                        }

                        if not account_data['account_number'] or not account_data['bank_code']:
                            self.logger.warning(f"Row {i}: Missing required fields. Skipping row.")
                            continue

                        account = Account.from_dict(account_data)
                        accounts.append(account)
                    except Exception as e:
                        self.logger.warning(f"Error parsing row {i}: {str(e)}. Skipping row.")
                        continue

        except Exception as e:
            self.logger.error(f"Error parsing PesaLink CSV file: {str(e)}")
            raise

        self.logger.info(f"Successfully parsed {len(accounts)} accounts from PesaLink CSV file: {file_path}")
        return accounts

    def _parse_json(self, file_path: str) -> List[Account]:
        """
        Parse a JSON file to extract account information.

        Args:
            file_path (str): Path to the JSON file

        Returns:
            List[Account]: List of Account objects
        """
        accounts = []

        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)

                # Handle different JSON structures
                if isinstance(data, list):
                    # JSON is a list of accounts
                    accounts_data = data
                elif isinstance(data, dict) and 'accounts' in data:
                    # JSON has an 'accounts' key with a list of accounts
                    accounts_data = data.get('accounts', [])
                else:
                    # Unsupported JSON structure
                    raise ValueError(
                        "Unsupported JSON structure. Expected a list of accounts or an object with an 'accounts' key.")

                # Process each account
                for i, account_data in enumerate(accounts_data, start=1):
                    try:
                        # Create a reference ID if not provided
                        if not account_data.get('reference_id'):
                            account_data['reference_id'] = f"REF-{i}"

                        account = Account.from_dict(account_data)
                        accounts.append(account)
                    except Exception as e:
                        self.logger.warning(f"Error parsing account {i}: {str(e)}. Skipping account.")
                        continue

        except Exception as e:
            self.logger.error(f"Error parsing JSON file: {str(e)}")
            raise

        self.logger.info(f"Successfully parsed {len(accounts)} accounts from JSON file: {file_path}")
        return accounts

    def _parse_xml(self, file_path: str) -> List[Account]:
        """
        Parse an XML file to extract account information.

        Args:
            file_path (str): Path to the XML file

        Returns:
            List[Account]: List of Account objects
        """
        accounts = []

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Find all account elements
            account_elements = []

            # Try different possible structures
            if root.tag == 'accounts':
                account_elements = root.findall('account')
            else:
                account_elements = root.findall('.//account')

            if not account_elements:
                raise ValueError("No account elements found in XML file.")

            # Process each account element
            for i, account_elem in enumerate(account_elements, start=1):
                try:
                    account_data = {}

                    # Extract account details
                    for child in account_elem:
                        account_data[child.tag.lower()] = child.text

                    # Check required fields
                    if not account_data.get('account_number') or not account_data.get('bank_code'):
                        self.logger.warning(f"Missing required fields for account {i}. Skipping account.")
                        continue

                    # Create a reference ID if not provided
                    if not account_data.get('reference_id'):
                        account_data['reference_id'] = f"REF-{i}"

                    account = Account.from_dict(account_data)
                    accounts.append(account)
                except Exception as e:
                    self.logger.warning(f"Error parsing account {i}: {str(e)}. Skipping account.")
                    continue

        except Exception as e:
            self.logger.error(f"Error parsing XML file: {str(e)}")
            raise

        self.logger.info(f"Successfully parsed {len(accounts)} accounts from XML file: {file_path}")
        return accounts
    