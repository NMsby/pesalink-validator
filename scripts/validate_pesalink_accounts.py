"""
Bulk validation script for PesaLink accounts.
This script takes a PesaLink sample accounts file and validates all accounts.
"""
import os
import sys
import time
import logging
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to the path to import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api.pesalink_client import PesaLinkClient
from app.utils.pesalink_data_handler import PesaLinkDataHandler
from app.utils.logger import setup_logger
from app.core.processor import BatchProcessor
from app.models.validation_result import ValidationStatus
from app.reporting.report_generator import ReportGenerator
from app.reporting.notifier import Notifier


def validate_accounts_file(input_file: str, output_dir: str, batch_size: int,
                           workers: int, parallel: bool, notify: bool = False) -> Dict:
    """
    Validate all accounts in a PesaLink accounts file.

    Args:
        input_file (str): Path to the input file
        output_dir (str): Directory for output files
        batch_size (int): Maximum batch size
        workers (int): Number of worker threads
        parallel (bool): Whether to use parallel processing
        notify (bool): Whether to send email notifications

    Returns:
        Dict: Validation statistics
    """
    logger = logging.getLogger(__name__)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Create timestamp for output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: Convert PesaLink CSV to Account objects
    logger.info(f"Loading accounts from {input_file}")
    accounts = PesaLinkDataHandler.convert_to_accounts(input_file)
    logger.info(f"Loaded {len(accounts)} accounts")

    # Step 2: Process accounts in batches
    processor = BatchProcessor(
        max_batch_size=batch_size,
        worker_threads=workers,
        enable_parallel=parallel
    )

    logger.info(f"Starting account validation using batch size={batch_size}, workers={workers}, parallel={parallel}")
    start_time = time.time()
    results = processor.process(accounts)
    end_time = time.time()

    processing_time = end_time - start_time
    logger.info(f"Completed validation in {processing_time:.2f} seconds")

    # Step 3: Analyze results
    valid_results = [r for r in results if r.status == ValidationStatus.VALID]
    invalid_results = [r for r in results if r.status == ValidationStatus.INVALID]
    error_results = [r for r in results if r.status == ValidationStatus.ERROR]

    # Calculate statistics
    total = len(results)
    valid_count = len(valid_results)
    invalid_count = len(invalid_results)
    error_count = len(error_results)

    valid_percent = (valid_count / total) * 100 if total > 0 else 0
    invalid_percent = (invalid_count / total) * 100 if total > 0 else 0
    error_percent = (error_count / total) * 100 if total > 0 else 0

    logger.info(f"Validation results: {valid_count} valid ({valid_percent:.2f}%), "
                f"{invalid_count} invalid ({invalid_percent:.2f}%), "
                f"{error_count} errors ({error_percent:.2f}%)")

    # Step 4: Generate output files
    # 4.1: Convert validation results to dictionaries
    result_dicts = []
    for r in results:
        result_dict = {
            "accountNumber": r.account.account_number,
            "bankCode": r.account.bank_code,
            "status": "Valid" if r.status == ValidationStatus.VALID else "Invalid",
            "accountHolderName": r.validated_name if r.status == ValidationStatus.VALID else "",
            "bankName": r.bank_name or "",
            "currency": "KES"
        }

        # Add error information if applicable
        if r.status != ValidationStatus.VALID:
            result_dict["error"] = r.error_message

        result_dicts.append(result_dict)

    # 4.2: Save results to CSV
    combined_file = os.path.join(output_dir, f"validation_results_{timestamp}.csv")
    PesaLinkDataHandler.merge_validation_results(accounts, result_dicts, combined_file)

    # 4.3: Save valid accounts to CSV
    valid_file = os.path.join(output_dir, f"valid_accounts_{timestamp}.csv")
    valid_accounts = [r.account for r in valid_results]
    PesaLinkDataHandler.convert_to_csv(valid_accounts, valid_file)

    # 4.4: Save invalid accounts to CSV
    invalid_file = os.path.join(output_dir, f"invalid_accounts_{timestamp}.csv")
    invalid_accounts = [r.account for r in invalid_results]
    PesaLinkDataHandler.convert_to_csv(invalid_accounts, invalid_file)

    # 4.5: Save error accounts to CSV
    error_file = os.path.join(output_dir, f"error_accounts_{timestamp}.csv")
    error_accounts = [r.account for r in error_results]
    PesaLinkDataHandler.convert_to_csv(error_accounts, error_file)

    # 4.6: Save detailed results using ReportGenerator
    report_generator = ReportGenerator(output_dir=output_dir, output_format='json')
    report_files = report_generator.generate(results)

    # 4.7: Save summary to JSON
    summary = {
        "timestamp": timestamp,
        "input_file": input_file,
        "total_accounts": total,
        "valid_accounts": valid_count,
        "invalid_accounts": invalid_count,
        "error_accounts": error_count,
        "valid_percent": valid_percent,
        "invalid_percent": invalid_percent,
        "error_percent": error_percent,
        "processing_time_seconds": processing_time,
        "processing_rate": total / processing_time if processing_time > 0 else 0,
        "batch_size": batch_size,
        "workers": workers,
        "parallel": parallel,
        "output_files": {
            "combined": combined_file,
            "valid": valid_file,
            "invalid": invalid_file,
            "error": error_file,
            **report_files
        }
    }

    summary_file = os.path.join(output_dir, f"validation_summary_{timestamp}.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Generated output files:")
    logger.info(f"  Combined results: {combined_file}")
    logger.info(f"  Valid accounts: {valid_file}")
    logger.info(f"  Invalid accounts: {invalid_file}")
    logger.info(f"  Error accounts: {error_file}")
    logger.info(f"  Summary: {summary_file}")

    # Step 5: Send notification if requested
    if notify:
        notifier = Notifier()
        stats = {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "error": error_count,
            "valid_percent": valid_percent,
            "invalid_percent": invalid_percent,
            "error_percent": error_percent
        }
        notifier.notify_completion(summary["output_files"], stats)

    return summary


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Bulk validation for PesaLink accounts")
    parser.add_argument("--input", "-i", required=True, help="Path to the input CSV file")
    parser.add_argument("--output", "-o", default="output", help="Output directory for results")
    parser.add_argument("--batch-size", "-b", type=int, default=100,
                        help="Maximum batch size")
    parser.add_argument("--workers", "-w", type=int, default=10,
                        help="Number of worker threads")
    parser.add_argument("--parallel", "-p", action="store_true",
                        help="Enable parallel processing")
    parser.add_argument("--notify", "-n", action="store_true",
                        help="Send email notification when complete")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting PesaLink Bulk Account Validator")

    try:
        # Validate the accounts
        summary = validate_accounts_file(
            args.input,
            args.output,
            args.batch_size,
            args.workers,
            args.parallel,
            args.notify
        )

        # Print the final summary
        print("\nValidation Summary:")
        print(f"Total Accounts: {summary['total_accounts']}")
        print(f"Valid Accounts: {summary['valid_accounts']} ({summary['valid_percent']:.2f}%)")
        print(f"Invalid Accounts: {summary['invalid_accounts']} ({summary['invalid_percent']:.2f}%)")
        print(f"Error Accounts: {summary['error_accounts']} ({summary['error_percent']:.2f}%)")
        print(f"Processing Time: {summary['processing_time_seconds']:.2f} seconds")
        print(f"Processing Rate: {summary['processing_rate']:.2f} accounts per second")
        print(f"\nOutput files available in: {args.output}")

        return 0

    except Exception as e:
        logger.error(f"Error during validation: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
