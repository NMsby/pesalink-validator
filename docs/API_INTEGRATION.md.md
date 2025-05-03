# PesaLink API Integration

This document provides details on how our Bulk Account Validator integrates with the PesaLink Account Validation API.

## API Overview

The PesaLink Account Validation API allows applications to validate bank accounts before initiating transactions. The integration is crucial for preventing AC-01 errors (invalid account errors) in bulk payment processing.

### Base URL

```
https://account-validation-service.dev.pesalink.co.ke
```

## API Key Management

The application obtains an API key from the PesaLink API itself using the `/api/key` endpoint. This key is then used for authenticating all subsequent requests.

### Authentication

All API requests (except the key retrieval) use Bearer token authentication:

```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### 1. Retrieve API Key

**Endpoint:** `/api/key`  
**Method:** GET  
**Description:** Fetches the API Key for authentication.

**Sample Request:**
```bash
curl -X 'GET' 'https://account-validation-service.dev.pesalink.co.ke/api/key' -H 'accept: application/json'
```

**Sample Response:**
```json
{
  "apiKey": "609dab841280674f1a780272f59e9e4e"
}
```

### 2. Validate Account

**Endpoint:** `/api/validate`  
**Method:** POST  
**Description:** Validates an account using account number and bank code.

**Request Parameters:**
```json
{
  "accountNumber": "123456789",
  "bankCode": "ABC"
}
```

**Successful Response:**
```json
{
  "accountNumber": "123456789",
  "bankCode": "ABC",
  "status": "Valid",
  "accountHolderName": "John Doe",
  "bankName": "Sample Bank",
  "currency": "KES"
}
```

**Error Responses:**
- 400: Bad request, missing or invalid parameters
- 404: Account or bank not found

### 3. Download Sample Data

**Endpoint:** `/download/{fileName}`  
**Method:** GET  
**Description:** Downloads a CSV file of sample account data.

**Sample Request:**
```bash
curl -X 'GET' 'https://account-validation-service.dev.pesalink.co.ke/download/sample_1000' -H 'Authorization: Bearer YOUR_API_KEY'
```

**Sample Response:**
A CSV file containing sample account data will be downloaded.

## Integration in the Bulk Validator

### PesaLink API Client

Our application implements a dedicated client (`PesaLinkClient`) for communicating with the PesaLink API. This client handles:

1. **API Key Management**: Automatically fetches and refreshes the API key
2. **Authentication**: Adds the necessary headers to all requests
3. **Error Handling**: Processes API errors and maps them to internal error codes
4. **Retry Logic**: Implements exponential backoff for transient errors

### Validation Process

The validation process follows these steps:

1. Fetch the API key if not already available
2. Format the account data according to the API requirements
3. Make a validation request to the `/api/validate` endpoint
4. Process the response:
   - If valid, extract account holder name and other details
   - If invalid, map the error to an internal error code
5. Return a `ValidationResult` object with the validation outcome

### Error Handling

The API client maps PesaLink error responses to internal error codes:

| HTTP Status   | Error Type   | Internal Error Code  |
|---------------|--------------|----------------------|
| 400           | Bad Request  | INVALID_REQUEST      |
| 404 (account) | Not Found    | ACCOUNT_NOT_FOUND    |
| 404 (bank)    | Not Found    | BANK_NOT_FOUND       |
| 401/403       | Unauthorized | AUTHENTICATION_ERROR |
| 429           | Rate Limit   | RATE_LIMIT_ERROR     |
| 5xx           | Server Error | API_ERROR            |

### Configuration

The API integration can be configured through environment variables or the `.env` file:

```
PESALINK_API_BASE_URL=https://account-validation-service.dev.pesalink.co.ke
PESALINK_API_KEY=your_api_key_here  # Optional, will be fetched if not provided
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=2
```

## Testing the API Integration

A dedicated test script is provided to verify the API integration:

```bash
python test_scripts/test_pesalink_api.py --key --validate --account 123456789 --bank ABC
```

This script tests:
1. API key retrieval
2. Account validation
3. Error handling

## Mock API for Development

For development and testing purposes, a mock PesaLink API is included. This allows you to test the application without connecting to the real PesaLink API.

### Starting the Mock API

To start the mock API server:

```bash
./test_scripts/run_mock_api.sh
```

This will start a local server on port 5000 that simulates the PesaLink API.

To run the server in the background:

```bash
./test_scripts/run_mock_api.sh --background
```

### Using the Mock API

To use the mock API, set the following environment variable:

```
PESALINK_API_BASE_URL=http://localhost:5000
```

All API requests will now be directed to the mock server instead of the real PesaLink API.

### Mock API Features

The mock API simulates the following features:

1. **API Key Retrieval**: Returns a consistent mock API key
2. **Account Validation**: Validates accounts against a predefined list of valid accounts
3. **Error Handling**: Simulates various error scenarios (invalid accounts, closed accounts, etc.)
4. **Sample Data Generation**: Provides sample account data for testing

### Predefined Test Accounts

The mock API includes several predefined test accounts:

| Account Number | Bank Code | Status   | Account Holder Name |
|----------------|-----------|----------|---------------------|
| 1234567890     | 01        | ACTIVE   | John Doe            |
| 5555555555     | 01        | ACTIVE   | Alice Johnson       |
| 9876543210     | 02        | ACTIVE   | Jane Smith          |
| 1111222233     | 03        | ACTIVE   | Bob Williams        |
| 2468135790     | 03        | INACTIVE | Grace Taylor        |
| 1357924680     | 04        | CLOSED   | Henry Anderson      |
| 8765432109     | 05        | BLOCKED  | Frank Wilson        |

For accounts not in this list, the mock API will randomly determine if they are valid (with a 70% chance of being valid).

### Simulating Network Conditions

The mock API introduces a small random delay (100–500 ms) to simulate real-world network conditions.

### Logs

The mock API logs all requests and responses to `logs/mock_api.log`. This can be helpful for debugging issues with the API integration.

```
PESALINK_API_BASE_URL=http://localhost:5000
```

## Potential Improvements

1. **Caching**: Implement a cache for validation results to avoid redundant API calls
2. **Bulk Validation**: If PesaLink adds a bulk validation endpoint, update the client to use it
3. **Webhook Support**: Add support for asynchronous validation using webhooks
4. **Token Refresh**: Implement automatic refresh of expired tokens
