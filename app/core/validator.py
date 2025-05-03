"""
Core validation logic for account validation.
"""
import logging
import concurrent.futures
from typing import List, Dict, Any, Optional

from app.models.account import Account
from app.models.validation_result import ValidationResult, ValidationStatus
from app.api.pesalink_client import PesaLinkClient
from app.core.error_handler import ErrorHandler, ErrorCode
from app.utils.logger import LoggerMixin
import app.config as config

logger = logging.getLogger(__name__)


class AccountValidator(LoggerMixin):
    """Handles account validation logic."""

    def __init__(self, use_parallel=True, worker_threads=None):
        """
        Initialize the AccountValidator.

        Args:
            use_parallel (bool): Whether to use parallel processing
            worker_threads (int): Number of worker threads for parallel processing
        """
        self.pesalink_client = PesaLinkClient()
        self.error_handler = ErrorHandler()
        self.use_parallel = use_parallel and config.ENABLE_PARALLEL_PROCESSING
        self.worker_threads = worker_threads or config.WORKER_THREADS

    def validate_single(self, account: Account) -> ValidationResult:
        """
        Validate a single account.

        Args:
            account (Account): The account to validate

        Returns:
            ValidationResult: The validation result
        """
        self.logger.debug(f"Validating account: {account.account_number}")

        try:
            # Perform basic format validation first
            if not self._validate_format(account):
                return ValidationResult(
                    account=account,
                    status=ValidationStatus.INVALID,
                    error_code=ErrorCode.INVALID_FORMAT.value,
                    error_message="Account number format is invalid"
                )

            # Validate through PesaLink API
            return self.pesalink_client.validate_account(account)

        except Exception as e:
            self.logger.error(f"Error validating account {account.account_number}: {str(e)}")
            return ValidationResult(
                account=account,
                status=ValidationStatus.ERROR,
                error_code=ErrorCode.UNKNOWN_ERROR.value,
                error_message=str(e)
            )

    def validate_batch(self, accounts: List[Account]) -> List[ValidationResult]:
        """
        Validate a batch of accounts.

        Args:
            accounts (List[Account]): List of accounts to validate

        Returns:
            List[ValidationResult]: List of validation results
        """
        self.logger.info(f"Validating batch of {len(accounts)} accounts")

        # If parallel processing is disabled, validate sequentially
        if not self.use_parallel:
            return [self.validate_single(account) for account in accounts]

        # Use parallel processing with thread pool
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.worker_threads) as executor:
            # Submit all validation tasks
            future_to_account = {
                executor.submit(self.validate_single, account): account
                for account in accounts
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_account):
                account = future_to_account[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error validating account {account.account_number}: {str(e)}")
                    results.append(ValidationResult(
                        account=account,
                        status=ValidationStatus.ERROR,
                        error_code=ErrorCode.UNKNOWN_ERROR.value,
                        error_message=str(e)
                    ))

        return results

    def _validate_format(self, account: Account) -> bool:
        """
        Validate the format of an account number.

        Args:
            account (Account): The account to validate

        Returns:
            bool: True if the format is valid, False otherwise
        """
        # Basic format validation logic
        if not account.account_number:
            return False

        if not account.bank_code:
            return False

        # Additional format validation rules could be added here,
        # For example,
        # - Check account number length based on bank code
        # - Check if account number contains only digits
        # - Validate, according to specific bank's account number format

        return True

    def pre_validate_batch(self, accounts: List[Account]) -> Dict[str, List[Account]]:
        """
        Perform pre-validation checks on a batch of accounts.

        Args:
            accounts (List[Account]): List of accounts to validate

        Returns:
            Dict[str, List[Account]]: Dictionary with valid and invalid accounts
        """
        valid_accounts = []
        invalid_accounts = []

        for account in accounts:
            if self._validate_format(account):
                valid_accounts.append(account)
            else:
                invalid_accounts.append(account)

        self.logger.info(f"Pre-validation: {len(valid_accounts)} valid format, {len(invalid_accounts)} invalid format")

        return {
            "valid": valid_accounts,
            "invalid": invalid_accounts
        }

    def check_validation_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Check the status of a validation request.

        Args:
            request_id (str): The request ID to check

        Returns:
            Optional[Dict[str, Any]]: Status information or None if error
        """
        try:
            # This would use a different API endpoint in a real implementation.
            # For now, we'll return a mock response
            return {
                "request_id": request_id,
                "status": "completed",
                "timestamp": "2025-05-03T14:35:45.123Z"
            }
        except Exception as e:
            self.logger.error(f"Error checking validation status for {request_id}: {str(e)}")
            return None
