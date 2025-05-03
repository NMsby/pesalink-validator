"""
Utility to analyze the PesaLink sample account data file.
This script helps understand the structure and content of the sample data.
"""
import os
import sys
import csv
import argparse
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime

# Add the parent directory to the path to import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logger import setup_logger
from app.utils.pesalink_data_handler import PesaLinkDataHandler


def analyze_csv_file(file_path: str) -> dict:
    """
    Analyze a CSV file containing account data.

    Args:
        file_path (str): Path to the CSV file

    Returns:
        dict: Analysis results
    """
    print(f"Analyzing file: {file_path}")

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return None

    # Initialize analysis data
    analysis = {
        "file_name": os.path.basename(file_path),
        "file_size": os.path.getsize(file_path),
        "total_rows": 0,
        "columns": [],
        "sample_rows": [],
        "bank_codes": Counter(),
        "account_number_length": Counter(),
        "missing_values": defaultdict(int)
    }

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            # Read header row
            reader = csv.reader(csvfile)
            header = next(reader)
            analysis["columns"] = header

            # Process data rows
            for i, row in enumerate(reader, start=1):
                analysis["total_rows"] += 1

                # Store sample rows (first 5)
                if i <= 5:
                    sample_row = dict(zip(header, row))
                    analysis["sample_rows"].append(sample_row)

                # Process row data for analysis
                if len(header) == len(row):
                    row_dict = dict(zip(header, row))

                    # Count bank codes
                    bank_code = row_dict.get("Bank Code", "")
                    if bank_code:
                        analysis["bank_codes"][bank_code] += 1
                    else:
                        analysis["missing_values"]["Bank Code"] += 1

                    # Analyze account number length
                    account_number = row_dict.get("Account Number", "")
                    if account_number:
                        analysis["account_number_length"][len(account_number)] += 1
                    else:
                        analysis["missing_values"]["Account Number"] += 1
                else:
                    print(f"Warning: Row {i} has {len(row)} columns, expected {len(header)}")

    except Exception as e:
        print(f"Error analyzing file: {str(e)}")
        return None

    # Convert Counter objects to dictionaries for JSON serialization
    analysis["bank_codes"] = dict(analysis["bank_codes"])
    analysis["account_number_length"] = dict(analysis["account_number_length"])
    analysis["missing_values"] = dict(analysis["missing_values"])

    return analysis


def generate_test_data(analysis: dict, output_file: str, count: int = 50) -> str:
    """
    Generate a test data file based on the analysis.

    Args:
        analysis (dict): Analysis results
        output_file (str): Path to the output file
        count (int): Number of test records to generate

    Returns:
        str: Path to the generated file
    """
    if not analysis:
        print("Error: No analysis data provided")
        return None

    print(f"Generating test data file with {count} records: {output_file}")

    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Create a subset of the original data
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=analysis["columns"])
            writer.writeheader()

            # Get the original file path
            original_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "sample_data",
                analysis["file_name"]
            )

            # Open original file and sample records
            with open(original_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)

                # Sample records
                records = []
                for i, row in enumerate(reader):
                    if i < count:
                        records.append(row)
                    else:
                        break

                # Write sampled records
                for record in records:
                    writer.writerow(record)

        print(f"Generated test data file: {output_file}")
        return output_file

    except Exception as e:
        print(f"Error generating test data: {str(e)}")
        return None


def analyze_content(analysis: dict):
    """
    Perform deeper analysis on the content of the CSV file.

    Args:
        analysis (dict): Basic analysis results

    Returns:
        dict: Enhanced analysis results
    """
    # Identify the most common bank codes
    top_banks = sorted(analysis["bank_codes"].items(), key=lambda x: x[1], reverse=True)
    analysis["top_banks"] = [{"code": code, "count": count} for code, count in top_banks[:5]]

    # Calculate account number format statistics
    account_lengths = analysis["account_number_length"]
    analysis["account_length_stats"] = {
        "min_length": min(map(int, account_lengths.keys())) if account_lengths else 0,
        "max_length": max(map(int, account_lengths.keys())) if account_lengths else 0,
        "most_common_length": max(account_lengths.items(), key=lambda x: x[1])[0] if account_lengths else 0
    }

    # Calculate data quality metrics
    total_rows = analysis["total_rows"]
    missing_values = analysis["missing_values"]
    analysis["data_quality"] = {
        "complete_rows_percent": 100 - (sum(missing_values.values()) / total_rows * 100) if total_rows > 0 else 0,
        "missing_fields": missing_values
    }

    return analysis


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Analyze PesaLink sample account data")
    parser.add_argument("--file", default="sample_data/sample_1000_accounts.csv", help="Path to the sample CSV file")
    parser.add_argument("--output", default="analysis_results.json", help="Path to the output analysis file")
    parser.add_argument("--generate", action="store_true", help="Generate a test data file")
    parser.add_argument("--count", type=int, default=50, help="Number of test records to generate")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(log_level)

    # Analyze the file
    analysis = analyze_csv_file(args.file)

    if analysis:
        # Perform deeper analysis
        analysis = analyze_content(analysis)

        # Print summary
        print("\nAnalysis Summary:")
        print(f"File: {analysis['file_name']}")
        print(f"Size: {analysis['file_size']} bytes")
        print(f"Total Rows: {analysis['total_rows']}")
        print(f"Columns: {', '.join(analysis['columns'])}")

        print("\nBank Codes Distribution:")
        for bank, count in sorted(analysis["bank_codes"].items(), key=lambda x: x[1], reverse=True):
            print(f"  {bank}: {count} accounts ({count / analysis['total_rows'] * 100:.2f}%)")

        print("\nAccount Number Length Distribution:")
        for length, count in sorted(analysis["account_number_length"].items()):
            print(f"  {length} characters: {count} accounts ({count / analysis['total_rows'] * 100:.2f}%)")

        print("\nMissing Values:")
        for column, count in analysis["missing_values"].items():
            print(f"  {column}: {count} rows ({count / analysis['total_rows'] * 100:.2f}%)")

        print("\nData Quality:")
        print(f"  Complete Rows: {analysis['data_quality']['complete_rows_percent']:.2f}%")

        # Save analysis to file
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)

        print(f"\nSaved detailed analysis to: {args.output}")

        # Generate test data if requested
        if args.generate:
            test_file = os.path.join("sample_data", f"test_{args.count}_accounts.csv")
            generate_test_data(analysis, test_file, args.count)

    return 0


if __name__ == "__main__":
    sys.exit(main())
