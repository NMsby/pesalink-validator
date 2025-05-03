"""
Load test script for the Bulk Account Validator.
This script tests the performance of the system under different loads.
"""
import os
import sys
import time
import csv
import random
import string
import argparse
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to the path to import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logger import setup_logger
from app.core.processor import BatchProcessor
from app.utils.pesalink_data_handler import PesaLinkDataHandler


def generate_random_account_number(length=10):
    """Generate a random account number."""
    # 80% chance of valid account number (only digits)
    if random.random() < 0.8:
        return ''.join(random.choices(string.digits, k=length))

    # 20% chance of invalid account number
    invalid_types = [
        # Too short
        lambda: ''.join(random.choices(string.digits, k=random.randint(2, 5))),
        # Too long
        lambda: ''.join(random.choices(string.digits, k=random.randint(20, 30))),
        # Contains non-digits
        lambda: ''.join(random.choices(string.digits + string.ascii_letters, k=length)),
        # Contains special characters
        lambda: ''.join(random.choices(string.digits, k=length - 1)) + random.choice('-_.,'),
        # Empty string
        lambda: ''
    ]

    return random.choice(invalid_types)()


def generate_random_bank_code():
    """Generate a random bank code."""
    # 80% chance of valid bank code (01-05)
    if random.random() < 0.8:
        return f"{random.randint(1, 5):02d}"

    # 20% chance of invalid bank code
    invalid_types = [
        # Out of range
        lambda: f"{random.randint(6, 99):02d}",
        # Contains non-digits
        lambda: random.choice(string.ascii_letters) + str(random.randint(1, 9)),
        # Empty string
        lambda: ''
    ]

    return random.choice(invalid_types)()


def generate_test_data(output_file, num_accounts):
    """Generate test data with random accounts."""
    print(f"Generating test data with {num_accounts} accounts: {output_file}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(["Account Number", "Bank Code"])

        # Write accounts
        for _ in range(num_accounts):
            account_number = generate_random_account_number()
            bank_code = generate_random_bank_code()
            writer.writerow([account_number, bank_code])

    print(f"Test data generated: {output_file}")
    return output_file


def run_validation_test(input_file, batch_size, workers, parallel):
    """Run a validation test with the given parameters."""
    print(f"Running test: batch_size={batch_size}, workers={workers}, parallel={parallel}")

    try:
        # Load accounts
        accounts = PesaLinkDataHandler.convert_to_accounts(input_file)
        print(f"Loaded {len(accounts)} accounts from {input_file}")

        # Create processor
        processor = BatchProcessor(
            max_batch_size=batch_size,
            worker_threads=workers,
            enable_parallel=parallel
        )

        # Process accounts
        start_time = time.time()
        results = processor.process(accounts)
        end_time = time.time()

        # Calculate statistics
        processing_time = end_time - start_time
        processing_rate = len(accounts) / processing_time if processing_time > 0 else 0

        # Count results by status
        valid_count = sum(1 for r in results if r.status.value == 'valid')
        invalid_count = sum(1 for r in results if r.status.value == 'invalid')
        error_count = sum(1 for r in results if r.status.value == 'error')

        return {
            "batch_size": batch_size,
            "workers": workers,
            "parallel": parallel,
            "total_accounts": len(accounts),
            "valid_accounts": valid_count,
            "invalid_accounts": invalid_count,
            "error_accounts": error_count,
            "processing_time": processing_time,
            "processing_rate": processing_rate
        }

    except Exception as e:
        print(f"Error running test: {str(e)}")
        return {
            "batch_size": batch_size,
            "workers": workers,
            "parallel": parallel,
            "error": str(e)
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Load test for Bulk Account Validator")
    parser.add_argument("--generate", action="store_true", help="Generate test data")
    parser.add_argument("--accounts", type=int, default=1000, help="Number of accounts to generate")
    parser.add_argument("--file", default="sample_data/load_test.csv", help="Test data file")
    parser.add_argument("--output", default="test_results.csv", help="Test results output file")
    parser.add_argument("--batch-sizes", default="100,500,1000", help="Comma-separated list of batch sizes to test")
    parser.add_argument("--workers-list", default="1,5,10,20", help="Comma-separated list of worker counts to test")
    parser.add_argument("--iterations", type=int, default=3, help="Number of test iterations")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(log_level)

    # Generate test data if requested
    if args.generate:
        generate_test_data(args.file, args.accounts)

    # Parse test parameters
    batch_sizes = [int(x) for x in args.batch_sizes.split(",")]
    workers_list = [int(x) for x in args.workers_list.split(",")]

    # Ensure test data file exists
    if not os.path.exists(args.file):
        print(f"Error: Test data file not found: {args.file}")
        print("Use --generate to create test data")
        return 1

    # Run tests
    results = []

    # Sequential tests
    for batch_size in batch_sizes:
        for _ in range(args.iterations):
            result = run_validation_test(args.file, batch_size, 1, False)
            result["test_type"] = "sequential"
            results.append(result)

    # Parallel tests
    for batch_size in batch_sizes:
        for workers in workers_list:
            for _ in range(args.iterations):
                result = run_validation_test(args.file, batch_size, workers, True)
                result["test_type"] = "parallel"
                results.append(result)

    # Save results to CSV
    with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
        if not results:
            print("No test results to save")
            return 0

        # Get fieldnames from the first result
        fieldnames = list(results[0].keys())

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow(result)

    print(f"Test results saved to {args.output}")

    # Print summary
    print("\nTest Summary:")

    # Sequential tests
    seq_results = [r for r in results if r["test_type"] == "sequential"]
    if seq_results:
        seq_times = [r["processing_time"] for r in seq_results if "processing_time" in r]
        seq_rates = [r["processing_rate"] for r in seq_results if "processing_rate" in r]

        if seq_times and seq_rates:
            avg_time = sum(seq_times) / len(seq_times)
            avg_rate = sum(seq_rates) / len(seq_rates)

            print(f"Sequential: Avg Time: {avg_time:.2f}s, Avg Rate: {avg_rate:.2f} accounts/s")

    # Parallel tests by worker count
    print("\nParallel Tests by Worker Count:")
    for workers in workers_list:
        worker_results = [r for r in results if r["test_type"] == "parallel" and r["workers"] == workers]
        if worker_results:
            worker_times = [r["processing_time"] for r in worker_results if "processing_time" in r]
            worker_rates = [r["processing_rate"] for r in worker_results if "processing_rate" in r]

            if worker_times and worker_rates:
                avg_time = sum(worker_times) / len(worker_times)
                avg_rate = sum(worker_rates) / len(worker_rates)

                print(f"Workers {workers}: Avg Time: {avg_time:.2f}s, Avg Rate: {avg_rate:.2f} accounts/s")

    # Calculate speedup
    if seq_results and "processing_time" in seq_results[0]:
        seq_avg_time = sum(r["processing_time"] for r in seq_results if "processing_time" in r) / len(seq_results)

        for workers in workers_list:
            worker_results = [r for r in results if r["test_type"] == "parallel" and r["workers"] == workers]
            if worker_results and "processing_time" in worker_results[0]:
                worker_avg_time = sum(r["processing_time"] for r in worker_results if "processing_time" in r) / len(
                    worker_results)
                speedup = seq_avg_time / worker_avg_time if worker_avg_time > 0 else 0

                print(f"Speedup with {workers} workers: {speedup:.2f}x")

    return 0


if __name__ == "__main__":
    sys.exit(main())
