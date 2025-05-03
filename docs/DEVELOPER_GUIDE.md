# PesaLink Bulk Account Validator - Developer Guide

This guide provides information for developers who want to maintain, extend, or customize the PesaLink Bulk Account Validator.

## Project Structure

```
pesalink-validator/
│
├── app/                        # Main application package
│   ├── __init__.py
│   ├── main.py                 # Main entry point
│   ├── config.py               # Configuration settings
│   ├── api/                    # API integration
│   │   ├── __init__.py
│   │   └── pesalink_client.py  # PesaLink API client
│   ├── core/                   # Core functionality
│   │   ├── __init__.py
│   │   ├── validator.py        # Account validation logic
│   │   ├── processor.py        # Batch processing logic
│   │   └── error_handler.py    # Error handling
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── account.py          # Account model
│   │   ├── validation_result.py# Validation result model
│   │   └── batch.py            # Batch model
│   ├── utils/                  # Utilities
│   │   ├── __init__.py
│   │   ├── file_parser.py      # File parsing
│   │   ├── file_writer.py      # File writing
│   │   ├── logger.py           # Logging
│   │   ├── security.py         # Security utilities
│   │   └── pesalink_data_handler.py  # PesaLink data format handler
│   └── reporting/              # Reporting
│       ├── __init__.py
│       ├── report_generator.py # Report generation
│       └── notifier.py         # Notification service
│
├── scripts/                    # Utility scripts
│   ├── run_validation.sh       # Validation script
│   └── validate_pesalink_accounts.py  # PesaLink validation script
│
├── test_scripts/               # Testing scripts
│   ├── analyze_sample_data.py  # Sample data analyzer
│   ├── load_test.py            # Load testing
│   ├── mock_pesalink_api.py    # Mock API server
│   ├── run_api_test.sh         # API test runner
│   ├── run_tests.sh            # Test suite runner
│   └── test_pesalink_api.py    # API test script
│
├── docs/                       # Documentation
│   ├── API_INTEGRATION.md      # API integration details
│   ├── USER_GUIDE.md           # User guide
│   └── DEVELOPER_GUIDE.md      # This file
│
├── sample_data/                # Sample data
│   └── test_50_accounts.csv    # Test accounts
│
├── .env.example                # Example environment variables
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
└── README.md                   # Project overview
```

## Architecture

The application follows a modular architecture with clear separation of concerns:

### Core Components

1. **Data Models**: Define the structure of accounts, validation results, and batches
2. **API Client**: Handles communication with the PesaLink API
3. **Validator**: Implements the validation logic
4. **Processor**: Manages batch processing and parallel execution
5. **File Handling**: Parses input files and generates output reports
6. **Reporting**: Creates reports and sends notifications

### Data Flow

1. Input file is parsed into Account objects
2. Accounts are divided into batches
3. Each batch is processed by the validator
4. Validation results are collected
5. Reports are generated based on the results

## Development Environment

### Setting Up

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

3. Install development dependencies:
   ```
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8 isort
   ```

4. Set up pre-commit hooks (optional):
   ```
   pip install pre-commit
   pre-commit install
   ```

### Running Tests

Run the comprehensive test suite:
```
./test_scripts/run_tests.sh
```

Run individual tests:
```
# API test
python test_scripts/test_pesalink_api.py --key --validate

# Load test
python test_scripts/load_test.py --generate --accounts 100
```

### Code Style

The project follows the PEP 8 style guide with some customizations:

- Line length: 100 characters
- Docstrings: Google style
- Import order: standard library, third-party, local

To format the code:
```
black app scripts test_scripts
isort app scripts test_scripts
flake8 app scripts test_scripts
```

## Extending the Application

### Adding a New Feature

1. Identify the appropriate module for your feature
2. Implement the feature following the existing patterns
3. Add tests for the new functionality
4. Update documentation

### Example: Adding a New Input Format

To add support for a new input format (e.g., YAML):

1. Install the required dependency:
   ```
   pip install pyyaml
   ```

2. Update `app/utils/file_parser.py`:
   ```python
   def parse(self, file_path: str) -> List[Account]:
       # ...
       elif ext == '.yaml' or ext == '.yml':
           return self._parse_yaml(file_path)
       # ...
   
   def _parse_yaml(self, file_path: str) -> List[Account]:
       """Parse a YAML file to extract account information."""
       import yaml
       
       accounts = []
       
       try:
           with open(file_path, 'r', encoding='utf-8') as yamlfile:
               data = yaml.safe_load(yamlfile)
               
               # Process YAML data...
               
               return accounts
       except Exception as e:
           self.logger.error(f"Error parsing YAML file: {str(e)}")
           raise
   ```

3. Update the command-line parser in `app/main.py`:
   ```python
   def parse_arguments():
       # ...
       parser.add_argument('--format', '-f', 
                        choices=['csv', 'json', 'xml', 'yaml'], 
                        default='csv',
                        help='Output format for reports')
       # ...
   ```

4. Add tests for the new format

### Example: Adding a New Report Type

To add a new report type (e.g., HTML report):

1. Update `app/reporting/report_generator.py`:
   ```python
   def generate(self, results: List[ValidationResult]) -> Dict[str, str]:
       # ...
       
       # HTML report
       if self.output_format == 'html' or self.output_format == 'all':
           html_file = os.path.join(self.output_dir, f"report_{timestamp}.html")
           self._generate_html_report(results, html_file)
           report_files['html'] = html_file
       
       # ...
   
   def _generate_html_report(self, results: List[ValidationResult], file_path: str) -> str:
       """Generate an HTML report."""
       # Implementation here...
   ```

2. Update the command-line parser in `app/main.py`:
   ```python
   def parse_arguments():
       # ...
       parser.add_argument('--format', '-f', 
                        choices=['csv', 'json', 'xml', 'html', 'all'], 
                        default='csv',
                        help='Output format for reports')
       # ...
   ```

## Common Development Tasks

### Adding a New API Endpoint

If PesaLink adds a new API endpoint:

1. Update `app/api/pesalink_client.py` with the new endpoint
2. Add appropriate error handling
3. Update the API integration tests

### Modifying the Validation Logic

To modify how accounts are validated:

1. Update `app/core/validator.py`:
   ```python
   def validate_single(self, account: Account) -> ValidationResult:
       # Your new validation logic here
   ```

2. Update the error handling in `app/core/error_handler.py` if needed
3. Update tests to cover the new validation logic

### Adding a New Command-Line Option

To add a new command-line option:

1. Update `app/main.py`:
   ```python
   def parse_arguments():
       # ...
       parser.add_argument('--new-option', action='store_true',
                          help='Description of the new option')
       # ...
   
   def main():
       # ...
       if args.new_option:
           # Implement the new option's functionality
       # ...
   ```

2. Update the shell script in `scripts/run_validation.sh`
3. Update the documentation

## Performance Optimization

### Profiling

To profile the application:

```python
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(20)  # Print top 20 functions by cumulative time
    return result

# Usage
profile_function(processor.process, accounts)
```

### Memory Optimization

For handling very large files:

1. Use generators to process data streams instead of loading everything into memory
2. Implement chunked file reading in `app/utils/file_parser.py`
3. Add memory monitoring to the batch processor

### Parallelization Strategies

The application uses threading for parallelization. For even better performance:

1. Consider using multiprocessing for CPU-bound tasks
2. Implement asynchronous I/O for network-bound tasks
3. Add distributed processing support for very large workloads

## Troubleshooting Development Issues

### API Integration Issues

1. Check the API documentation for changes
2. Use the `--verbose` flag to see detailed API communication
3. Test with the mock API to isolate client-side issues

### Performance Issues

1. Profile the application to identify bottlenecks
2. Monitor memory usage during batch processing
3. Test with different batch sizes and worker counts

### Dependency Issues

1. Use a virtual environment to isolate dependencies
2. Pin dependencies to specific versions in `requirements.txt`
3. Document any special dependency requirements

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

Please follow these guidelines:
- Write tests for new functionality
- Update documentation
- Follow the code style guidelines
- Include a clear description of your changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.
