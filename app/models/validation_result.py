"""
Validation result model for representing the outcome of account validation.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from app.models.account import Account


class ValidationStatus(Enum):
    """Enumeration of possible validation statuses."""
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class ValidationResult:
    """Represents the result of an account validation."""
    account: Account
    status: ValidationStatus
    validated_name: Optional[str] = None
    account_status: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    bank_name: Optional[str] = None

    def to_dict(self):
        """
        Convert the ValidationResult object to a dictionary.

        Returns:
            dict: Dictionary representation of the validation result
        """
        result = {
            "account_number": self.account.account_number,
            "bank_code": self.account.bank_code,
            "reference_id": self.account.reference_id,
            "status": self.status.value,
            "original_name": self.account.account_name,
            "validated_name": self.validated_name,
            "account_status": self.account_status,
            "bank_name": self.bank_name
        }

        if self.status in (ValidationStatus.INVALID, ValidationStatus.ERROR):
            result["error_code"] = self.error_code
            result["error_message"] = self.error_message

        return result

    def is_valid(self):
        """
        Check if the account is valid.

        Returns:
            bool: True if the account is valid, False otherwise
        """
        return self.status == ValidationStatus.VALID

    def __str__(self):
        """String representation of the validation result."""
        if self.status == ValidationStatus.VALID:
            return f"Valid Account: {self.account.account_number} ({self.validated_name or 'unnamed'})"
        elif self.status == ValidationStatus.INVALID:
            return f"Invalid Account: {self.account.account_number}, Error: {self.error_code} - {self.error_message}"
        elif self.status == ValidationStatus.ERROR:
            return f"Error validating {self.account.account_number}: {self.error_message}"
        else:
            return f"Pending validation: {self.account.account_number}"
        