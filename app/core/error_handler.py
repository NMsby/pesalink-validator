"""
Error handling module for managing validation errors from the PesaLink API.
"""
import logging
from enum import Enum
from typing import Dict, Optional, Any

from app.utils.logger import LoggerMixin

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Enumeration of error codes used in the system."""

    # Format errors
    INVALID_FORMAT = "INVALID_FORMAT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_BANK_CODE = "INVALID_BANK_CODE"
    INVALID_ACCOUNT_NUMBER = "INVALID_ACCOUNT_NUMBER"

    # Account errors
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_BLOCKED = "ACCOUNT_BLOCKED"

    # System errors
    API_ERROR = "API_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"

    # PesaLink specific errors
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    BANK_NOT_FOUND = "BANK_NOT_FOUND"
    INVALID_REQUEST = "INVALID_REQUEST"

    # Generic errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"

    @classmethod
    def get_description(cls, code: str) -> str:
        """
        Get a human-readable description for an error code.

        Args:
            code (str): Error code

        Returns:
            str: Error description
        """
        descriptions = {
            cls.INVALID_FORMAT.value: "The format of the account information is invalid.",
            cls.MISSING_FIELD.value: "Required field is missing.",
            cls.INVALID_BANK_CODE.value: "Bank code is invalid or unrecognized.",
            cls.INVALID_ACCOUNT_NUMBER.value: "Account number format is invalid.",

            cls.ACCOUNT_NOT_FOUND.value: "Account does not exist.",
            cls.ACCOUNT_INACTIVE.value: "Account is inactive.",
            cls.ACCOUNT_CLOSED.value: "Account is closed.",
            cls.ACCOUNT_BLOCKED.value: "Account is blocked.",

            cls.API_ERROR.value: "API returned an error.",
            cls.CONNECTION_ERROR.value: "Connection to the API failed.",
            cls.TIMEOUT_ERROR.value: "Request to the API timed out.",
            cls.AUTHENTICATION_ERROR.value: "Authentication with the API failed.",
            cls.RATE_LIMIT_ERROR.value: "API rate limit exceeded.",

            cls.INVALID_ACCOUNT.value: "The account is invalid or cannot be validated.",
            cls.BANK_NOT_FOUND.value: "The specified bank was not found.",
            cls.INVALID_REQUEST.value: "The request format was invalid.",

            cls.UNKNOWN_ERROR.value: "An unknown error occurred."
        }

        return descriptions.get(code, f"Error code: {code}")

    @classmethod
    def map_pesalink_error(cls, status_code: int, message: str) -> str:
        """
        Map a PesaLink API error to our internal error code.

        Args:
            status_code (int): HTTP status code
            message (str): Error message

        Returns:
            str: Internal error code
        """
        if status_code == 400:
            return cls.INVALID_REQUEST.value
        elif status_code == 404:
            if "account" in message.lower():
                return cls.ACCOUNT_NOT_FOUND.value
            elif "bank" in message.lower():
                return cls.BANK_NOT_FOUND.value
            else:
                return cls.INVALID_ACCOUNT.value
        elif status_code == 401 or status_code == 403:
            return cls.AUTHENTICATION_ERROR.value
        elif status_code == 429:
            return cls.RATE_LIMIT_ERROR.value
        elif status_code >= 500:
            return cls.API_ERROR.value
        else:
            return cls.UNKNOWN_ERROR.value


class ErrorHandler(LoggerMixin):
    """Handles errors during the validation process."""

    def handle_error(self, error_code: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle an error with the given code and message.

        Args:
            error_code (str): Error code
            error_message (str, optional): Error message

        Returns:
            Dict[str, Any]: Error information
        """
        # Log the error
        self.logger.error(f"Error: {error_code} - {error_message or ErrorCode.get_description(error_code)}")

        # Return error information
        return {
            "error_code": error_code,
            "error_message": error_message or ErrorCode.get_description(error_code)
        }

    def handle_api_error(self, status_code: int, response_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an API error from the response.

        Args:
            status_code (int): HTTP status code
            response_body (Dict[str, Any]): API response body

        Returns:
            Dict[str, Any]: Error information
        """
        # Extract the error message from the API response
        error_message = response_body.get("message", response_body.get("error", "Unknown API error"))

        # Map the API error to our internal error code
        internal_error_code = ErrorCode.map_pesalink_error(status_code, error_message)

        # Log and return error information
        return self.handle_error(internal_error_code, error_message)

    def handle_validation_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a validation response from the API.

        Args:
            response (Dict[str, Any]): API validation response

        Returns:
            Dict[str, Any]: Processed validation information
        """
        # Check if the response indicates a valid account
        status = response.get("status")

        if status == "Valid":
            return {
                "is_valid": True,
                "account_holder_name": response.get("accountHolderName"),
                "bank_name": response.get("bankName"),
                "currency": response.get("currency", "KES")
            }
        else:
            # For invalid accounts, determine the reason
            error_code = ErrorCode.INVALID_ACCOUNT.value
            error_message = f"Account validation failed: {status}"

            return {
                "is_valid": False,
                "error_code": error_code,
                "error_message": error_message
            }

    def handle_exception(self, exception: Exception) -> Dict[str, Any]:
        """
        Handle an exception.

        Args:
            exception (Exception): The exception to handle

        Returns:
            Dict[str, Any]: Error information
        """
        # Determine the error type based on exception
        if isinstance(exception, TimeoutError):
            return self.handle_error(ErrorCode.TIMEOUT_ERROR.value, str(exception))
        elif isinstance(exception, ConnectionError):
            return self.handle_error(ErrorCode.CONNECTION_ERROR.value, str(exception))
        else:
            return self.handle_error(ErrorCode.UNKNOWN_ERROR.value, str(exception))

    def classify_error(self, error_code: str) -> str:
        """
        Classify an error code into a category.

        Args:
            error_code (str): Error code to classify

        Returns:
            str: Error category
        """
        format_errors = [
            ErrorCode.INVALID_FORMAT.value,
            ErrorCode.MISSING_FIELD.value,
            ErrorCode.INVALID_BANK_CODE.value,
            ErrorCode.INVALID_ACCOUNT_NUMBER.value,
            ErrorCode.INVALID_REQUEST.value
        ]

        account_errors = [
            ErrorCode.ACCOUNT_NOT_FOUND.value,
            ErrorCode.ACCOUNT_INACTIVE.value,
            ErrorCode.ACCOUNT_CLOSED.value,
            ErrorCode.ACCOUNT_BLOCKED.value,
            ErrorCode.INVALID_ACCOUNT.value,
            ErrorCode.BANK_NOT_FOUND.value
        ]

        system_errors = [
            ErrorCode.API_ERROR.value,
            ErrorCode.CONNECTION_ERROR.value,
            ErrorCode.TIMEOUT_ERROR.value,
            ErrorCode.AUTHENTICATION_ERROR.value,
            ErrorCode.RATE_LIMIT_ERROR.value
        ]

        if error_code in format_errors:
            return "FORMAT_ERROR"
        elif error_code in account_errors:
            return "ACCOUNT_ERROR"
        elif error_code in system_errors:
            return "SYSTEM_ERROR"
        else:
            return "OTHER_ERROR"
