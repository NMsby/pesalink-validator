"""
Client for interacting with the PesaLink Account Validation API.
Handles account validation using the actual PesaLink API endpoints.
"""
import os
import logging
import time
import json
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from typing import Dict, List, Optional, Any, Union

from app.models.account import Account
from app.models.validation_result import ValidationResult, ValidationStatus
from app.utils.logger import LoggerMixin
import app.config as config

logger = logging.getLogger(__name__)


class PesaLinkClient(LoggerMixin):
    """Client for interacting with the PesaLink API."""

    def __init__(self):
        """Initialize the PesaLink API client."""
        self.base_url = config.PESALINK_API_BASE_URL
        self.api_key = config.PESALINK_API_KEY
        self.timeout = config.REQUEST_TIMEOUT
        self.max_retries = config.MAX_RETRIES
        self.retry_delay = config.RETRY_DELAY

    def _fetch_api_key(self):
        """
        Fetch the API key from the PesaLink API.

        Returns:
            str: API key

        Raises:
            Exception: If fetching API key fails
        """
        try:
            self.logger.info("Fetching API key from PesaLink")
            response = requests.get(
                f"{self.base_url}/api/key",
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            api_key = data.get("apiKey")

            if not api_key:
                self.logger.error("API key not found in response")
                raise ValueError("API key not found in response")

            self.logger.info("Successfully fetched API key")
            return api_key

        except Exception as e:
            self.logger.error(f"Failed to fetch API key: {str(e)}")
            raise

    def _get_api_key(self):
        """
        Get API key, fetching from the API if needed.

        Returns:
            str: API key
        """
        if not self.api_key:
            self.api_key = self._fetch_api_key()
        return self.api_key

    def _make_request(self, method, endpoint, data=None, params=None, headers=None):
        """
        Make a request to the PesaLink API with retry logic.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            data (dict, optional): Request body data
            params (dict, optional): Query parameters
            headers (dict, optional): Request headers

        Returns:
            dict: API response

        Raises:
            Exception: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"

        if not headers:
            headers = {}

        # Add authorization header with the API key
        headers.update({
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Making {method} request to {endpoint}")

                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )

                # Log response status and abbreviated content for debugging
                content_preview = str(response.content)[:200] + "..." if len(response.content) > 200 else str(
                    response.content)
                self.logger.debug(f"API Response: Status={response.status_code}, Content={content_preview}")

                response.raise_for_status()
                return response.json() if response.content else {}

            except (ConnectionError, Timeout) as e:
                self.logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    self.logger.error(f"Max retries exceeded for request to {url}")
                    raise

            except RequestException as e:
                status_code = e.response.status_code if hasattr(e, 'response') and hasattr(e.response,
                                                                                           'status_code') else 'N/A'

                # For 4xx errors, don't retry
                if hasattr(e, 'response') and 400 <= e.response.status_code < 500:
                    self.logger.error(f"Request failed with status {status_code}: {str(e)}")
                    return e.response.json() if hasattr(e, 'response') and e.response.content else {"error": str(e)}

                # For 5xx errors, retry
                self.logger.warning(f"Request attempt {attempt + 1} failed with status {status_code}: {str(e)}")
                if attempt < self.max_retries - 1:
                    sleep_time = self.retry_delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    self.logger.error(f"Max retries exceeded for request to {url}")
                    raise

    def validate_account(self, account: Account) -> ValidationResult:
        """
        Validate an account through the PesaLink API.

        Args:
            account (Account): The account to validate

        Returns:
            ValidationResult: The result of the validation
        """
        self.logger.debug(f"Validating account: {account.account_number} at bank {account.bank_code}")

        try:
            request_data = {
                "accountNumber": account.account_number,
                "bankCode": account.bank_code
            }

            response = self._make_request("POST", "/api/validate", data=request_data)

            if "error" in response:
                return ValidationResult(
                    account=account,
                    status=ValidationStatus.ERROR,
                    error_code="API_ERROR",
                    error_message=response.get("error", "Unknown API error")
                )

            # Process successful response
            # Check if status is "Valid" (according to the API documentation)
            if response.get("status") == "Valid":
                return ValidationResult(
                    account=account,
                    status=ValidationStatus.VALID,
                    validated_name=response.get("accountHolderName"),
                    account_status="ACTIVE",  # Assuming Valid status implies an Active account
                    bank_name=response.get("bankName")
                )
            else:
                # If the status is not "Valid", treat as an invalid account
                return ValidationResult(
                    account=account,
                    status=ValidationStatus.INVALID,
                    error_code="INVALID_ACCOUNT",
                    error_message=response.get("status", "Account validation failed")
                )

        except Exception as e:
            self.logger.error(f"Error validating account {account.account_number}: {str(e)}")
            return ValidationResult(
                account=account,
                status=ValidationStatus.ERROR,
                error_code="EXCEPTION",
                error_message=str(e)
            )

    def validate_accounts_batch(self, accounts: List[Account]) -> List[ValidationResult]:
        """
        Validate a batch of accounts through the PesaLink API.

        Args:
            accounts (list): List of Account objects to validate

        Returns:
            list: List of ValidationResult objects
        """
        self.logger.info(f"Validating batch of {len(accounts)} accounts")

        # The API doesn't support bulk validation, so we validate accounts individually
        results = []
        for account in accounts:
            result = self.validate_account(account)
            results.append(result)

        return results

    def download_sample_accounts(self, file_name: str, output_path: str) -> Optional[str]:
        """
        Download a sample accounts file from the PesaLink API.

        Args:
            file_name (str): The name of the file to download (e.g., 'sample_1000')
            output_path (str): The path where to save the downloaded file

        Returns:
            str: Path to the downloaded file or None if download failed
        """
        self.logger.info(f"Downloading sample accounts file: {file_name}")

        try:
            url = f"{self.base_url}/download/{file_name}"
            headers = {
                "Authorization": f"Bearer {self._get_api_key()}"
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )

            response.raise_for_status()

            # Ensure output directory exists
            os.makedirs(output_path, exist_ok=True)

            # Save the file
            output_file = f"{output_path}/{file_name}_accounts.csv"
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info(f"Successfully downloaded sample accounts file to {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"Error downloading sample accounts file: {str(e)}")
            return None
