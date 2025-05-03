"""
Report generation logic for creating validation reports.
"""
import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.models.validation_result import ValidationResult, ValidationStatus
from app.utils.file_writer import FileWriter
from app.utils.logger import LoggerMixin
import app.config as config

logger = logging.getLogger(__name__)


class ReportGenerator(LoggerMixin):
    """Generates reports based on validation results."""

    def __init__(self, output_dir=None, output_format='csv'):
        """
        Initialize the ReportGenerator.

        Args:
            output_dir (str): Directory for output reports
            output_format (str): Format for output reports (csv, JSON, XML)
        """
        self.output_dir = output_dir or config.DEFAULT_OUTPUT_DIR
        self.output_format = output_format.lower()
        self.file_writer = FileWriter()

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, results: List[ValidationResult]) -> Dict[str, str]:
        """
        Generate reports from validation results.

        Args:
            results (List[ValidationResult]): List of validation results

        Returns:
            Dict[str, str]: Dictionary of report types and file paths
        """
        if not results:
            self.logger.warning("No results provided for report generation.")
            return {}

        self.logger.info(f"Generating reports for {len(results)} validation results")

        # Create timestamp for file names
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate reports
        report_files = {}

        # Summary report
        summary_data = self._generate_summary_data(results)
        summary_file = os.path.join(self.output_dir, f"summary_{timestamp}.{self.output_format}")
        report_files['summary'] = self._write_report(summary_data, summary_file)

        # Valid accounts report
        valid_results = [r for r in results if r.status == ValidationStatus.VALID]
        if valid_results:
            valid_data = [self._format_result(r) for r in valid_results]
            valid_file = os.path.join(self.output_dir, f"valid_accounts_{timestamp}.{self.output_format}")
            report_files['valid'] = self._write_report(valid_data, valid_file)

        # Invalid accounts report
        invalid_results = [r for r in results if r.status == ValidationStatus.INVALID]
        if invalid_results:
            invalid_data = [self._format_result(r) for r in invalid_results]
            invalid_file = os.path.join(self.output_dir, f"invalid_accounts_{timestamp}.{self.output_format}")
            report_files['invalid'] = self._write_report(invalid_data, invalid_file)

        # Error report
        error_results = [r for r in results if r.status == ValidationStatus.ERROR]
        if error_results:
            error_data = [self._format_result(r) for r in error_results]
            error_file = os.path.join(self.output_dir, f"error_accounts_{timestamp}.{self.output_format}")
            report_files['error'] = self._write_report(error_data, error_file)

        # All results report
        all_data = [self._format_result(r) for r in results]
        all_file = os.path.join(self.output_dir, f"all_accounts_{timestamp}.{self.output_format}")
        report_files['all'] = self._write_report(all_data, all_file)

        # Generate PesaLink format reports
        pesalink_valid_file = os.path.join(self.output_dir, f"pesalink_valid_{timestamp}.csv")
        valid_accounts = [r.account for r in valid_results]
        report_files['pesalink_valid'] = self.file_writer.write_pesalink_csv(valid_accounts, pesalink_valid_file)

        pesalink_invalid_file = os.path.join(self.output_dir, f"pesalink_invalid_{timestamp}.csv")
        invalid_accounts = [r.account for r in invalid_results]
        report_files['pesalink_invalid'] = self.file_writer.write_pesalink_csv(invalid_accounts, pesalink_invalid_file)

        # Generate statistics JSON
        stats = self._generate_statistics(results)
        stats_file = os.path.join(self.output_dir, f"statistics_{timestamp}.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        report_files['statistics'] = stats_file

        self.logger.info(f"Generated {len(report_files)} reports")

        return report_files

    def _generate_summary_data(self, results: List[ValidationResult]) -> List[Dict]:
        """
        Generate summary data from validation results.

        Args:
            results (List[ValidationResult]): List of validation results

        Returns:
            List[Dict]: Summary data
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

        # Sort error codes by frequency
        sorted_error_codes = [
            {"code": code, "count": count, "percentage": (count / total) * 100 if total > 0 else 0}
            for code, count in sorted(error_codes.items(), key=lambda x: x[1], reverse=True)
        ]

        # Create summary data
        summary = [
            {
                "category": "Total Accounts",
                "count": total,
                "percentage": 100.0
            },
            {
                "category": "Valid Accounts",
                "count": valid_count,
                "percentage": valid_percent
            },
            {
                "category": "Invalid Accounts",
                "count": invalid_count,
                "percentage": invalid_percent
            },
            {
                "category": "Error Accounts",
                "count": error_count,
                "percentage": error_percent
            }
        ]

        # Add error code breakdown
        for error_code in sorted_error_codes:
            summary.append({
                "category": f"Error Code: {error_code['code']}",
                "count": error_code['count'],
                "percentage": error_code['percentage']
            })

        return summary

    def _format_result(self, result: ValidationResult) -> Dict:
        """
        Format a validation result for reporting.

        Args:
            result (ValidationResult): Validation result to format

        Returns:
            Dict: Formatted result
        """
        formatted = result.to_dict()

        # Add additional fields for reporting
        if result.status == ValidationStatus.VALID:
            formatted["validation_status"] = "Valid"
        elif result.status == ValidationStatus.INVALID:
            formatted["validation_status"] = "Invalid"
            formatted["reason"] = result.error_message
        else:
            formatted["validation_status"] = "Error"
            formatted["reason"] = result.error_message

        return formatted

    def _write_report(self, data, file_path):
        """
        Write report data to a file.

        Args:
            data: Data to write
            file_path: Path to write to

        Returns:
            str: Path to the written file
        """
        if not data:
            self.logger.warning(f"No data to write to {file_path}")
            return None

        try:
            if self.output_format == 'csv':
                return self.file_writer.write_csv(data, file_path)
            elif self.output_format == 'json':
                return self.file_writer.write_json(data, file_path)
            elif self.output_format == 'xml':
                return self.file_writer.write_xml(data, file_path)
            else:
                self.logger.warning(f"Unsupported output format: {self.output_format}, defaulting to CSV")
                return self.file_writer.write_csv(data, file_path)
        except Exception as e:
            self.logger.error(f"Error writing report to {file_path}: {str(e)}")
            raise

    def _generate_statistics(self, results: List[ValidationResult]) -> Dict:
        """
        Generate detailed statistics from validation results.

        Args:
            results (List[ValidationResult]): List of validation results

        Returns:
            Dict: Statistics dictionary
        """
        total = len(results)
        valid_results = [r for r in results if r.status == ValidationStatus.VALID]
        invalid_results = [r for r in results if r.status == ValidationStatus.INVALID]
        error_results = [r for r in results if r.status == ValidationStatus.ERROR]

        valid_count = len(valid_results)
        invalid_count = len(invalid_results)
        error_count = len(error_results)

        # Calculate percentages
        valid_percent = (valid_count / total) * 100 if total > 0 else 0
        invalid_percent = (invalid_count / total) * 100 if total > 0 else 0
        error_percent = (error_count / total) * 100 if total > 0 else 0

        # Group by bank
        banks = {}
        for r in results:
            bank_code = r.account.bank_code
            if bank_code not in banks:
                banks[bank_code] = {
                    "total": 0,
                    "valid": 0,
                    "invalid": 0,
                    "error": 0
                }

            banks[bank_code]["total"] += 1

            if r.status == ValidationStatus.VALID:
                banks[bank_code]["valid"] += 1
            elif r.status == ValidationStatus.INVALID:
                banks[bank_code]["invalid"] += 1
            else:
                banks[bank_code]["error"] += 1

        # Calculate bank percentages
        for bank_code, stats in banks.items():
            stats["valid_percent"] = (stats["valid"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            stats["invalid_percent"] = (stats["invalid"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            stats["error_percent"] = (stats["error"] / stats["total"]) * 100 if stats["total"] > 0 else 0

        # Group error codes
        error_codes = {}
        for r in results:
            if r.status in (ValidationStatus.INVALID, ValidationStatus.ERROR) and r.error_code:
                if r.error_code not in error_codes:
                    error_codes[r.error_code] = {
                        "count": 0,
                        "percentage": 0,
                        "examples": []
                    }

                error_codes[r.error_code]["count"] += 1

                # Add example if we have fewer than 5
                if len(error_codes[r.error_code]["examples"]) < 5:
                    error_codes[r.error_code]["examples"].append({
                        "account_number": r.account.account_number,
                        "bank_code": r.account.bank_code,
                        "message": r.error_message
                    })

        # Calculate error code percentages
        for code, stats in error_codes.items():
            stats["percentage"] = (stats["count"] / total) * 100 if total > 0 else 0

        # Generate timestamp
        timestamp = datetime.now().isoformat()

        return {
            "timestamp": timestamp,
            "total_accounts": total,
            "valid_accounts": valid_count,
            "invalid_accounts": invalid_count,
            "error_accounts": error_count,
            "valid_percent": valid_percent,
            "invalid_percent": invalid_percent,
            "error_percent": error_percent,
            "banks": banks,
            "error_codes": error_codes
        }
