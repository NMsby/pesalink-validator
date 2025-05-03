"""
Configuration settings for the Bulk Account Validator application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
PESALINK_API_BASE_URL = os.getenv("PESALINK_API_BASE_URL", "https://account-validation-service.dev.pesalink.co.ke")
PESALINK_API_KEY = os.getenv("PESALINK_API_KEY")  # Will be fetched from API if not provided

# Processing Configuration
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "1000"))
WORKER_THREADS = int(os.getenv("WORKER_THREADS", "10"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))

# Security Configuration
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
TOKEN_EXPIRY = int(os.getenv("TOKEN_EXPIRY", "3600"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/validator.log")

# Feature Flags
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "True").lower() == "true"
ENABLE_PARALLEL_PROCESSING = os.getenv("ENABLE_PARALLEL_PROCESSING", "True").lower() == "true"

# Email Notification Configuration (Optional)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")
NOTIFICATION_EMAILS = os.getenv("NOTIFICATION_EMAILS", "[]")

# File paths and directories
DEFAULT_OUTPUT_DIR = os.getenv("DEFAULT_OUTPUT_DIR", "output")
SAMPLE_DATA_DIR = os.getenv("SAMPLE_DATA_DIR", "sample_data")

# Validate required configuration
if not ENCRYPTION_KEY:
    import secrets
    print("Warning: ENCRYPTION_KEY not set in environment. Generating temporary key.")
    ENCRYPTION_KEY = secrets.token_hex(16)
