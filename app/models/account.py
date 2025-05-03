"""
Account data model for representing account information.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Account:
    """Represents bank account information for validation."""
    account_number: str
    bank_code: str
    reference_id: str
    amount: float = 0.0
    currency: str = "KES"
    account_name: Optional[str] = None
    phone_number: Optional[str] = None
    transaction_type: Optional[str] = None

    @classmethod
    def from_dict(cls, data):
        """
        Create an Account object from a dictionary.

        Args:
            data (dict): Dictionary containing account information

        Returns:
            Account: New Account object
        """
        return cls(
            account_number=data.get("account_number"),
            bank_code=data.get("bank_code"),
            reference_id=data.get("reference_id", ""),
            amount=float(data.get("amount", 0.0)),
            currency=data.get("currency", "KES"),
            account_name=data.get("account_name"),
            phone_number=data.get("phone_number"),
            transaction_type=data.get("transaction_type")
        )

    def to_dict(self):
        """
        Convert the Account object to a dictionary.

        Returns:
            dict: Dictionary representation of the account
        """
        return {
            "account_number": self.account_number,
            "bank_code": self.bank_code,
            "reference_id": self.reference_id,
            "amount": self.amount,
            "currency": self.currency,
            "account_name": self.account_name,
            "phone_number": self.phone_number,
            "transaction_type": self.transaction_type
        }

    def validate_format(self):
        """
        Perform basic format validation on the account.

        Returns:
            bool: True if the format is valid, False otherwise
        """
        # Check if required fields are present
        if not self.account_number or not self.bank_code:
            return False

        # Validate account number (basic validation)
        if not isinstance(self.account_number, str):
            return False

        # Validate bank code (basic validation)
        if not isinstance(self.bank_code, str):
            return False

        return True

    def __str__(self):
        """String representation of the account."""
        masked_account = self.account_number[:2] + '*' * (len(self.account_number) - 6) + self.account_number[
                                                                                          -4:] if len(
            self.account_number) > 6 else '****'
        name_part = f", name: {self.account_name}" if self.account_name else ""
        return f"Account(number: {masked_account}, bank: {self.bank_code}{name_part})"
