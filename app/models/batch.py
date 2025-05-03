"""
Batch models for representing batches of accounts for validation.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from app.models.account import Account
from app.models.validation_result import ValidationResult


@dataclass
class Batch:
    """Represents a batch of accounts for validation."""
    accounts: List[Account]
    batch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    status: str = "pending"
    total_accounts: int = field(init=False)
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Initialize derived fields after object creation."""
        self.total_accounts = len(self.accounts)

    def mark_processed(self):
        """Mark the batch as processed."""
        self.processed_at = datetime.now()
        self.status = "processed"

    @classmethod
    def split(cls, batch, max_size):
        """
        Split a large batch into smaller batches.

        Args:
            batch (Batch): The batch to split
            max_size (int): Maximum number of accounts per batch

        Returns:
            list: List of Batch objects
        """
        if len(batch.accounts) <= max_size:
            return [batch]

        sub_batches = []
        for i in range(0, len(batch.accounts), max_size):
            sub_accounts = batch.accounts[i:i + max_size]
            sub_batch = cls(
                accounts=sub_accounts,
                metadata=batch.metadata.copy()
            )
            sub_batches.append(sub_batch)

        return sub_batches

    def to_dict(self):
        """
        Convert the Batch object to a dictionary.

        Returns:
            dict: Dictionary representation of the batch
        """
        return {
            "batch_id": self.batch_id,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "status": self.status,
            "total_accounts": self.total_accounts,
            "metadata": self.metadata
        }


@dataclass
class BatchValidationResult:
    """Represents the results of validating a batch of accounts."""
    batch_id: str
    results: List[ValidationResult]
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None

    def mark_completed(self):
        """Mark the batch validation as completed."""
        self.completed_at = datetime.now()
        self.processing_time = (self.completed_at - self.started_at).total_seconds()

    @property
    def total(self):
        """Get the total number of accounts in the batch."""
        return len(self.results)

    @property
    def valid_count(self):
        """Get the number of valid accounts in the batch."""
        from app.models.validation_result import ValidationStatus
        return sum(1 for r in self.results if r.status == ValidationStatus.VALID)

    @property
    def invalid_count(self):
        """Get the number of invalid accounts in the batch."""
        from app.models.validation_result import ValidationStatus
        return sum(1 for r in self.results if r.status == ValidationStatus.INVALID)

    @property
    def error_count(self):
        """Get the number of accounts with errors in the batch."""
        from app.models.validation_result import ValidationStatus
        return sum(1 for r in self.results if r.status == ValidationStatus.ERROR)

    @property
    def valid_results(self):
        """Get all valid validation results."""
        from app.models.validation_result import ValidationStatus
        return [r for r in self.results if r.status == ValidationStatus.VALID]

    @property
    def invalid_results(self):
        """Get all invalid validation results."""
        from app.models.validation_result import ValidationStatus
        return [r for r in self.results if r.status == ValidationStatus.INVALID]

    @property
    def error_results(self):
        """Get all validation results with errors."""
        from app.models.validation_result import ValidationStatus
        return [r for r in self.results if r.status == ValidationStatus.ERROR]

    def to_dict(self):
        """
        Convert the BatchValidationResult object to a dictionary.

        Returns:
            dict: Dictionary representation of the batch validation result
        """
        return {
            "batch_id": self.batch_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time": self.processing_time,
            "total": self.total,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "error_count": self.error_count
        }
