"""
Security utilities for handling sensitive data.
"""
import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import app.config as config
from app.utils.logger import LoggerMixin

logger = logging.getLogger(__name__)


class Security(LoggerMixin):
    """Handles security-related functions such as encryption and tokenization."""

    def __init__(self, key=None):
        """
        Initialize the Security utility.

        Args:
            key (str, optional): Encryption key
        """
        self.key = key or config.ENCRYPTION_KEY

        if not self.key:
            self.logger.warning("Encryption key not provided. Generating a temporary key.")
            self.key = Fernet.generate_key().decode('utf-8')

    def generate_key(self, password, salt=None):
        """
        Generate an encryption key from a password.

        Args:
            password (str): Password to derive key from
            salt (bytes, optional): Salt for key derivation

        Returns:
            bytes: Encryption key
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def encrypt(self, data):
        """
        Encrypt data.

        Args:
            data (str): Data to encrypt

        Returns:
            str: Encrypted data (base64-encoded)
        """
        if not data:
            return None

        try:
            f = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
            encrypted = f.encrypt(data.encode())
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error encrypting data: {str(e)}")
            raise

    def decrypt(self, encrypted_data):
        """
        Decrypt data.

        Args:
            encrypted_data (str): Encrypted data (base64-encoded)

        Returns:
            str: Decrypted data
        """
        if not encrypted_data:
            return None

        try:
            f = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
            decrypted = f.decrypt(base64.b64decode(encrypted_data))
            return decrypted.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Error decrypting data: {str(e)}")
            raise

    def mask_account_number(self, account_number):
        """
        Mask an account number for display.

        Args:
            account_number (str): Account number to mask

        Returns:
            str: Masked account number
        """
        if not account_number:
            return None

        if len(account_number) <= 4:
            return '*' * len(account_number)

        # Keep the first 2 and last 4 digits visible
        visible_start = 2
        visible_end = 4

        masked = account_number[:visible_start] + '*' * (len(account_number) - visible_start - visible_end) + account_number[-visible_end:]

        return masked

    def mask_sensitive_data(self, data):
        """
        Mask sensitive data in a dictionary.

        Args:
            data (dict): Dictionary containing sensitive data

        Returns:
            dict: Dictionary with sensitive data masked
        """
        if not data:
            return data

        masked_data = data.copy()

        sensitive_fields = [
            'account_number',
            'card_number',
            'cvv',
            'pin',
            'password',
            'id_number'
        ]

        for field in sensitive_fields:
            if field in masked_data and masked_data[field]:
                masked_data[field] = self.mask_account_number(str(masked_data[field]))

        return masked_data

    def hash_value(self, value, salt=None):
        """
        Create a hash of a value.

        Args:
            value (str): Value to hash
            salt (bytes, optional): Salt for hashing

        Returns:
            str: Base64-encoded hash
            bytes: Salt used for hashing
        """
        if not value:
            return None, None

        if salt is None:
            salt = os.urandom(16)

        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )

            hash_bytes = kdf.derive(value.encode())
            hash_value = base64.b64encode(hash_bytes).decode('utf-8')

            return hash_value, salt

        except Exception as e:
            self.logger.error(f"Error hashing value: {str(e)}")
            raise

    def verify_hash(self, value, hash_value, salt):
        """
        Verify a hash against a value.

        Args:
            value (str): Value to verify
            hash_value (str): Base64-encoded hash to verify against
            salt (bytes): Salt used for hashing

        Returns:
            bool: True if the hash matches the value, False otherwise
        """
        if not value or not hash_value or not salt:
            return False

        try:
            # Generate hash with the same salt
            new_hash, _ = self.hash_value(value, salt)

            # Compare hashes
            return new_hash == hash_value

        except Exception as e:
            self.logger.error(f"Error verifying hash: {str(e)}")
            return False

    def generate_secure_token(self, length=32):
        """
        Generate a secure random token.

        Args:
            length (int): Length of the token

        Returns:
            str: Secure random token
        """
        token_bytes = os.urandom(length)
        return base64.urlsafe_b64encode(token_bytes).decode('utf-8')[:length]
