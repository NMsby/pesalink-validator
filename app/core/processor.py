"""
Batch processing logic for validating accounts in batches.
"""
import time
import logging
from typing import List, Dict, Any, Optional

from app.core.validator import AccountValidator
from app.models.account import Account
from app.models.validation_result import ValidationResult, ValidationStatus
from app.models.batch import Batch, BatchValidationResult
from app.utils.logger import LoggerMixin
import app.config as config

logger = logging.getLogger(__name__)


class BatchProcessor(LoggerMixin):
    """Handles processing of account batches for validation."""

    def __init__(self, max_batch_size=None, worker_threads=None, enable_parallel=True):
        """
        Initialize the BatchProcessor.

        Args:
            max_batch_size (int): Maximum size of batches for processing
            worker_threads (int): Number of worker threads for parallel processing
            enable_parallel (bool): Whether to enable parallel processing
        """
        self.max_batch_size = max_batch_size or config.MAX_BATCH_SIZE
        self.worker_threads = worker_threads or config.WORKER_THREADS
        self.enable_parallel = enable_parallel and config.ENABLE_PARALLEL_PROCESSING
        self.validator = AccountValidator(
            use_parallel=self.enable_parallel,
            worker_threads=self.worker_threads
        )

    def process(self, accounts: List[Account]) -> List[ValidationResult]:
        """
        Process a list of accounts for validation.

        Args:
            accounts (List[Account]): List of accounts to validate

        Returns:
            List[ValidationResult]: List of validation results
        """
        if not accounts:
            self.logger.warning("No accounts provided for processing.")
            return []

        self.logger.info(f"Processing {len(accounts)} accounts (max_batch_size={self.max_batch_size}, "
                         f"parallel={self.enable_parallel}, workers={self.worker_threads})")

        start_time = time.time()

        # Create a batch for processing
        batch = Batch(accounts=accounts)

        # Process the batch
        result = self.process_batch(batch)

        end_time = time.time()
        processing_time = end_time - start_time

        self.logger.info(f"Processed {len(accounts)} accounts in {processing_time:.2f} seconds")
        self.logger.info(f"Results: {result.valid_count} valid, {result.invalid_count} invalid, "
                         f"{result.error_count} errors")

        return result.results

    def process_batch(self, batch: Batch) -> BatchValidationResult:
        """
        Process a batch of accounts for validation.

        Args:
            batch (Batch): Batch of accounts to validate

        Returns:
            BatchValidationResult: Results of the batch validation
        """
        self.logger.info(f"Processing batch {batch.batch_id} with {batch.total_accounts} accounts")

        # Split into smaller batches if needed
        if batch.total_accounts > self.max_batch_size:
            self.logger.info(f"Splitting batch into smaller batches (max_size={self.max_batch_size})")
            sub_batches = Batch.split(batch, self.max_batch_size)

            # Process each sub-batch
            all_results = []
            for i, sub_batch in enumerate(sub_batches):
                self.logger.info(f"Processing sub-batch {i + 1}/{len(sub_batches)} "
                                 f"({sub_batch.total_accounts} accounts)")
                sub_result = self.process_batch(sub_batch)
                all_results.extend(sub_result.results)

            # Create a combined result
            result = BatchValidationResult(
                batch_id=batch.batch_id,
                results=all_results
            )
            result.mark_completed()

            return result

        # Process the batch
        batch_result = BatchValidationResult(
            batch_id=batch.batch_id,
            results=[]
        )

        # Pre-validate accounts to filter out invalid ones
        pre_validation = self.validator.pre_validate_batch(batch.accounts)

        # Process invalid accounts (format errors)
        for account in pre_validation["invalid"]:
            batch_result.results.append(ValidationResult(
                account=account,
                status=ValidationStatus.INVALID,
                error_code="INVALID_FORMAT",
                error_message="Account format is invalid"
            ))

        # Validate accounts with valid format
        valid_format_results = self.validator.validate_batch(pre_validation["valid"])
        batch_result.results.extend(valid_format_results)

        # Mark the batch as processed
        batch.mark_processed()
        batch_result.mark_completed()

        self.logger.info(f"Completed batch {batch.batch_id}: {batch_result.valid_count} valid, "
                         f"{batch_result.invalid_count} invalid, {batch_result.error_count} errors")

        return batch_result

    def get_statistics(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Generate statistics from validation results.

        Args:
            results (List[ValidationResult]): List of validation results

        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        total = len(results)
        valid_count = sum(1 for r in results if r.status == ValidationStatus.VALID)
        invalid_count = sum(1 for r in results if r.status == ValidationStatus.INVALID)
        error_count = sum(1 for r in results if r.status == ValidationStatus.ERROR)

        # Calculate percentages
        valid_percent = (valid_count / total) * 100 if total > 0 else 0
        invalid_percent = (invalid_count / total) * 100 if total > 0 else 0
        error_percent = (error_count / total) * 100 if total > 0 else 0

        # Group error codes
        error_codes = {}
        for r in results:
            if r.status in (ValidationStatus.INVALID, ValidationStatus.ERROR) and r.error_code:
                error_codes[r.error_code] = error_codes.get(r.error_code, 0) + 1

        return {
            "total": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "error": error_count,
            "valid_percent": valid_percent,
            "invalid_percent": invalid_percent,
            "error_percent": error_percent,
            "error_codes": error_codes
        }

    def process_file(self, file_path: str) -> BatchValidationResult:
        """
        Process a file containing account information.

        Args:
            file_path (str): Path to the input file

        Returns:
            BatchValidationResult: Results of the batch validation
        """
        from app.utils.file_parser import FileParser

        # Parse the file
        file_parser = FileParser()
        accounts = file_parser.parse(file_path)

        # Create a batch
        batch = file_parser.create_batch(file_path)

        # Process the batch
        return self.process_batch(batch)
