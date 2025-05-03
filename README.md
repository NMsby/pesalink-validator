# PesaLink Bulk Account Validator

A system for validating bank accounts in bulk to prevent AC-01 errors before transaction processing.

## Overview

The PesaLink Bulk Account Validator is a solution for the PesaLink AI Fintech Hackathon challenge. It addresses the problem of invalid account errors (AC-01) in bulk payment processing by validating accounts before transactions are initiated.

The system accepts bulk files with account information, validates each account against the PesaLink API, and generates comprehensive reports identifying valid and invalid accounts with detailed error information.

## Features

- **Bulk Input Processing**: Accepts large volumes of payment instructions in CSV, JSON, or XML formats
- **Account Validation**: Validates account numbers against PesaLink's Account Validation API
- **Parallel Processing**: Optimizes validation through concurrent processing
- **Detailed Error Handling**: Provides clear reason codes for invalid accounts
- **Comprehensive Reporting**: Generates detailed reports of valid and invalid accounts
- **Security**: Protects sensitive account information through encryption and masking

## Project Status

🚧 **Under Development** 🚧

This project is currently being developed as part of the PesaLink AI Fintech Hackathon.

## Prerequisites

- Python 3.8+
- Internet connection to access the PesaLink API

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pesalink-validator.git
   cd pesalink-validator
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```
   cp .env.example .env
   # Edit .env file with your settings
   ```

## Usage

More detailed usage instructions will be provided as the project develops.

## License

[MIT License](LICENSE)

## Acknowledgements

- PesaLink for organizing the AI Fintech Hackathon
- Strathmore University for hosting the event