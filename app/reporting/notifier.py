"""
Notification service for sending alerts and notifications.
"""
import logging
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional, Any, Union

from app.utils.logger import LoggerMixin
import app.config as config

logger = logging.getLogger(__name__)


class Notifier(LoggerMixin):
    """Sends notifications about validation results."""

    def __init__(self):
        """Initialize the Notifier."""
        self.smtp_server = config.SMTP_SERVER if hasattr(config, 'SMTP_SERVER') else None
        self.smtp_port = config.SMTP_PORT if hasattr(config, 'SMTP_PORT') else 587
        self.smtp_username = config.SMTP_USERNAME if hasattr(config, 'SMTP_USERNAME') else None
        self.smtp_password = config.SMTP_PASSWORD if hasattr(config, 'SMTP_PASSWORD') else None
        self.from_email = config.FROM_EMAIL if hasattr(config, 'FROM_EMAIL') else None

        try:
            self.notification_emails = json.loads(config.NOTIFICATION_EMAILS) if hasattr(config,
                                                                                         'NOTIFICATION_EMAILS') else []
        except json.JSONDecodeError:
            self.logger.warning(
                f"Invalid NOTIFICATION_EMAILS format: {config.NOTIFICATION_EMAILS if hasattr(config, 'NOTIFICATION_EMAILS') else None}")
            self.notification_emails = []

    def send_email(self, to_emails: List[str], subject: str, body: str,
                   html_body: Optional[str] = None) -> bool:
        """
        Send an email notification.

        Args:
            to_emails (List[str]): List of email addresses to send to
            subject (str): Email subject
            body (str): Plain text email body
            html_body (str, optional): HTML email body

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.smtp_server or not self.smtp_username or not self.smtp_password or not self.from_email:
            self.logger.warning("Email notification is not configured. Skipping.")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)

            # Attach plain text body
            msg.attach(MIMEText(body, 'plain'))

            # Attach HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            self.logger.info(f"Email notification sent to {', '.join(to_emails)}")
            return True

        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
            return False

    def notify_completion(self, report_files: Dict[str, str], stats: Dict[str, Any]) -> bool:
        """
        Send a notification when validation is complete.

        Args:
            report_files (Dict[str, str]): Dictionary of report types and file paths
            stats (Dict[str, Any]): Statistics about the validation results

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if not self.notification_emails:
            self.logger.warning("No notification emails configured. Skipping completion notification.")
            return False

        subject = "PesaLink Bulk Account Validation Completed"

        body = f"""
        Account Validation Completed

        Summary:
        - Total Accounts: {stats.get('total', 0)}
        - Valid Accounts: {stats.get('valid', 0)} ({stats.get('valid_percent', 0):.2f}%)
        - Invalid Accounts: {stats.get('invalid', 0)} ({stats.get('invalid_percent', 0):.2f}%)
        - Errors: {stats.get('error', 0)} ({stats.get('error_percent', 0):.2f}%)

        Report Files:
        """

        for report_type, file_path in report_files.items():
            body += f"- {report_type.capitalize()}: {file_path}\n"

        # Create an HTML version
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .stats {{ margin-bottom: 20px; }}
                .stats table {{ border-collapse: collapse; width: 100%; }}
                .stats th, .stats td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .stats th {{ background-color: #f2f2f2; }}
                .reports {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <h1>Account Validation Completed</h1>

            <div class="stats">
                <h2>Summary</h2>
                <table>
                    <tr>
                        <th>Category</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                    <tr>
                        <td>Total Accounts</td>
                        <td>{stats.get('total', 0)}</td>
                        <td>100%</td>
                    </tr>
                    <tr>
                        <td>Valid Accounts</td>
                        <td>{stats.get('valid', 0)}</td>
                        <td>{stats.get('valid_percent', 0):.2f}%</td>
                    </tr>
                    <tr>
                        <td>Invalid Accounts</td>
                        <td>{stats.get('invalid', 0)}</td>
                        <td>{stats.get('invalid_percent', 0):.2f}%</td>
                    </tr>
                    <tr>
                        <td>Errors</td>
                        <td>{stats.get('error', 0)}</td>
                        <td>{stats.get('error_percent', 0):.2f}%</td>
                    </tr>
                </table>
            </div>

            <div class="reports">
                <h2>Report Files</h2>
                <ul>
        """

        for report_type, file_path in report_files.items():
            html_body += f"<li><strong>{report_type.capitalize()}:</strong> {file_path}</li>\n"

        html_body += """
                </ul>
            </div>
        </body>
        </html>
        """

        return self.send_email(self.notification_emails, subject, body, html_body)

    def notify_error(self, error_message: str, details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a notification when an error occurs.

        Args:
            error_message (str): Error message
            details (Dict[str, Any], optional): Additional error details

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if not self.notification_emails:
            self.logger.warning("No notification emails configured. Skipping error notification.")
            return False

        subject = "PesaLink Bulk Account Validation Error"

        body = f"""
        Account Validation Error

        Error: {error_message}
        """

        if details:
            body += "\nDetails:\n"
            for key, value in details.items():
                body += f"- {key}: {value}\n"

        # Create an HTML version
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .error {{ color: red; font-weight: bold; }}
                .details {{ margin-top: 20px; }}
                .details table {{ border-collapse: collapse; width: 100%; }}
                .details th, .details td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .details th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Account Validation Error</h1>

            <div class="error">
                <p>Error: {error_message}</p>
            </div>
        """

        if details:
            html_body += """
            <div class="details">
                <h2>Details</h2>
                <table>
                    <tr>
                        <th>Key</th>
                        <th>Value</th>
                    </tr>
            """

            for key, value in details.items():
                html_body += f"""
                    <tr>
                        <td>{key}</td>
                        <td>{value}</td>
                    </tr>
                """

            html_body += """
                </table>
            </div>
            """

        html_body += """
        </body>
        </html>
        """

        return self.send_email(self.notification_emails, subject, body, html_body)

    def notify_progress(self, current: int, total: int, status: str) -> bool:
        """
        Send a notification about progress.

        Args:
            current (int): Current progress
            total (int): Total items
            status (str): Status message

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        if not self.notification_emails:
            self.logger.warning("No notification emails configured. Skipping progress notification.")
            return False

        percent = (current / total) * 100 if total > 0 else 0

        subject = f"PesaLink Validation Progress: {percent:.2f}%"

        body = f"""
        Account Validation Progress

        Progress: {current}/{total} ({percent:.2f}%)
        Status: {status}
        """

        # Create an HTML version
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .progress-container {{ width: 100%; background-color: #f1f1f1; border-radius: 5px; }}
                .progress-bar {{ width: {percent}%; height: 30px; background-color: #4CAF50; border-radius: 5px; text-align: center; line-height: 30px; color: white; }}
            </style>
        </head>
        <body>
            <h1>Account Validation Progress</h1>

            <p>Status: {status}</p>

            <div class="progress-container">
                <div class="progress-bar">{percent:.2f}%</div>
            </div>

            <p>Processed {current} of {total} accounts</p>
        </body>
        </html>
        """

        return self.send_email(self.notification_emails, subject, body, html_body)
