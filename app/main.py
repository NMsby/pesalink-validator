"""
Main entry point for the Bulk Account Validator application.
"""
import argparse
import sys
import logging
import time
from typing import List, Dict

from app.utils.logger import setup_logger
from app.utils.file_parser import FileParser
from app.core.processor import BatchProcessor
from app.reporting.report_generator import ReportGenerator
from app.reporting.notifier import Notifier
from app.utils.pesalink_data_handler import PesaLinkDataHandler
import app.config as config

logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='PesaLink Bulk Account Validator')
    parser.add_argument('--input', '-i', required=True, help='Input file path (CSV, JSON, or XML)')
    parser.add_argument('--output', '-o', default=config.DEFAULT_OUTPUT_DIR, help='Output directory for reports')
    parser.add_argument('--format', '-f', choices=['csv', 'json', 'xml'], default='csv',
                        help='Output format for reports')
    parser.add_argument('--parallel', '-p', action='store_true',
                        help='Enable parallel processing')
    parser.add_argument('--batch-size', '-b', type=int, default=config.MAX_BATCH_SIZE,
                        help=f'Maximum batch size (default: {config.MAX_BATCH_SIZE})')
    parser.add_argument('--workers', '-w', type=int, default=config.WORKER_THREADS,
                        help=f'Number of worker threads (default: {config.WORKER_THREADS})')
    parser.add_argument('--notify', '-n', action='store_true',
                        help='Send email notification when complete')
    parser.add_argument('--pesalink', action='store_true',
                        help='Treat input as PesaLink format CSV')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')

    return parser.parse_args()


def main():
    """Main function to run the Bulk Account Validator."""
    args = parse_arguments()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else getattr(logging, config.LOG_LEVEL)
    setup_logger(log_level)

    logger.info("Starting PesaLink Bulk Account Validator")
    logger.info(f"Processing input file: {args.input}")

    start_time = time.time()

    try:
        # Load accounts from the input file
        if args.pesalink:
            # Use PesaLink format handler
            logger.info("Using PesaLink format handler")
            accounts = PesaLinkDataHandler.convert_to_accounts(args.input)
        else:
            # Use generic file parser
            logger.info("Using generic file parser")
            file_parser = FileParser()
            accounts = file_parser.parse(args.input)

        logger.info(f"Loaded {len(accounts)} accounts from input file")

        # Process accounts
        processor = BatchProcessor(
            max_batch_size=args.batch_size,
            worker_threads=args.workers,
            enable_parallel=args.parallel
        )

        logger.info(
            f"Starting validation with batch_size={args.batch_size}, workers={args.workers}, parallel={args.parallel}")
        results = processor.process(accounts)
        logger.info(f"Completed validation of {len(results)} accounts")

        # Generate reports
        report_generator = ReportGenerator(args.output, args.format)
        report_files = report_generator.generate(results)

        # Get processing statistics
        end_time = time.time()
        processing_time = end_time - start_time
        processing_rate = len(accounts) / processing_time if processing_time > 0 else 0

        # Print summary
        stats = processor.get_statistics(results)

        print("\nValidation Results:")
        print(f"Total Accounts: {stats['total']}")
        print(f"Valid Accounts: {stats['valid']} ({stats['valid_percent']:.2f}%)")
        print(f"Invalid Accounts: {stats['invalid']} ({stats['invalid_percent']:.2f}%)")
        print(f"Error Accounts: {stats['error']} ({stats['error_percent']:.2f}%)")
        print(f"\nProcessing Time: {processing_time:.2f} seconds")
        print(f"Processing Rate: {processing_rate:.2f} accounts per second")

        print("\nReport files generated:")
        for report_type, file_path in report_files.items():
            print(f"- {report_type}: {file_path}")

        # Send notification if requested
        if args.notify:
            logger.info("Sending completion notification")
            notifier = Notifier()
            notifier.notify_completion(report_files, stats)

        return 0

    except Exception as e:
        logger.error(f"Error during processing: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
