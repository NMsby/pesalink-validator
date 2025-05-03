"""
File writing utilities for creating output files in various formats.
"""
import os
import csv
import json
import logging
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from app.utils.logger import LoggerMixin

logger = logging.getLogger(__name__)


class FileWriter(LoggerMixin):
    """Writes data to output files in various formats (CSV, JSON, XML)."""

    def write_csv(self, data: List[Dict[str, Any]], file_path: str, headers: List[str] = None) -> str:
        """
        Write data to a CSV file.

        Args:
            data (List[Dict]): List of dictionaries to write
            file_path (str): Path to the output file
            headers (List[str], optional): Custom order of columns. If None, use all keys from the first row.

        Returns:
            str: Path to the created file
        """
        if not data:
            self.logger.warning("No data to write to CSV file.")
            return file_path

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Determine fieldnames
                if headers:
                    fieldnames = headers
                else:
                    # Get all keys from the first item
                    fieldnames = list(data[0].keys())

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for item in data:
                    # Only include fields that are in the headers
                    row = {k: item.get(k, '') for k in fieldnames}
                    writer.writerow(row)

            self.logger.info(f"Successfully wrote {len(data)} items to CSV file: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Error writing CSV file: {str(e)}")
            raise

    def write_json(self, data: List[Dict[str, Any]], file_path: str, pretty: bool = True) -> str:
        """
        Write data to a JSON file.

        Args:
            data (List[Dict]): List of dictionaries to write
            file_path (str): Path to the output file
            pretty (bool): Whether to format the JSON for readability

        Returns:
            str: Path to the created file
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                if pretty:
                    json.dump(data, jsonfile, indent=2)
                else:
                    json.dump(data, jsonfile)

            self.logger.info(f"Successfully wrote {len(data)} items to JSON file: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Error writing JSON file: {str(e)}")
            raise

    def write_xml(self, data: List[Dict[str, Any]], file_path: str, root_tag: str = 'accounts',
                  item_tag: str = 'account') -> str:
        """
        Write data to an XML file.

        Args:
            data (List[Dict]): List of dictionaries to write
            file_path (str): Path to the output file
            root_tag (str): Tag name for the root element
            item_tag (str): Tag name for each item element

        Returns:
            str: Path to the created file
        """
        if not data:
            self.logger.warning("No data to write to XML file.")
            return file_path

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            # Create root element
            root = ET.Element(root_tag)

            # Add each item as a child element
            for item in data:
                item_elem = ET.SubElement(root, item_tag)

                for key, value in item.items():
                    if value is not None:
                        child = ET.SubElement(item_elem, key)
                        child.text = str(value)

            # Pretty print XML
            rough_string = ET.tostring(root, 'utf-8')
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ")

            with open(file_path, 'w', encoding='utf-8') as xmlfile:
                xmlfile.write(pretty_xml)

            self.logger.info(f"Successfully wrote {len(data)} items to XML file: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Error writing XML file: {str(e)}")
            raise

    def write_pesalink_csv(self, accounts, file_path: str) -> str:
        """
        Write accounts to a CSV file in PesaLink format.

        Args:
            accounts: List of Account objects or dictionaries
            file_path (str): Path to the output file

        Returns:
            str: Path to the created file
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Account Number', 'Bank Code']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for account in accounts:
                    if hasattr(account, 'account_number'):
                        # Account object
                        row = {
                            'Account Number': account.account_number,
                            'Bank Code': account.bank_code
                        }
                    else:
                        # Dictionary
                        row = {
                            'Account Number': account.get('account_number', account.get('Account Number', '')),
                            'Bank Code': account.get('bank_code', account.get('Bank Code', ''))
                        }

                    writer.writerow(row)

            self.logger.info(f"Successfully wrote {len(accounts)} accounts to PesaLink CSV file: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Error writing PesaLink CSV file: {str(e)}")
            raise

    def write_validation_results(self, results, file_path: str, format: str = 'csv') -> str:
        """
        Write validation results to a file.

        Args:
            results: List of ValidationResult objects or dictionaries
            file_path (str): Path to the output file
            format (str): Output format (csv, JSON, XML)

        Returns:
            str: Path to the created file
        """
        # Convert results to dictionaries if they are objects
        data = []
        for result in results:
            if hasattr(result, 'to_dict'):
                data.append(result.to_dict())
            else:
                data.append(result)

        # Write to the specified format
        if format.lower() == 'csv':
            return self.write_csv(data, file_path)
        elif format.lower() == 'json':
            return self.write_json(data, file_path)
        elif format.lower() == 'xml':
            return self.write_xml(data, file_path, 'validation_results', 'result')
        else:
            raise ValueError(f"Unsupported output format: {format}")
