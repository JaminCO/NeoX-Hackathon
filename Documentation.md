# LianFlow Crypto Payment Gateway API Documentation

## Table of Contents
1. [Introduction](#1-introduction)
2. [Authentication](#2-authentication)
3. [Base URL](#3-base-url)
4. [API Endpoints](#4-api-endpoints)
    1. [Create Payment](#41-create-payment)
    2. [Get Payment Details](#42-get-payment-details)
    3. [Check Payment Status](#43-check-payment-status)
    4. [Get Transaction Details](#44-get-transaction-details)
5. [Webhook Integration](#5-webhook-integration)
6. [Error Handling](#6-error-handling)
7. [Code Examples](#7-code-examples)
8. [Support](#8-support)

## 1. Introduction
LianFlow Crypto Payment Gateway enables businesses to accept cryptocurrency payments seamlessly. This documentation provides comprehensive details about integrating our payment gateway into your applications.

## 2. Authentication
All API requests require authentication using an API key.

### To obtain your API key:
1. Sign up at [LianFlow Dashboard](https://dashboard.lianflow.com)
2. Navigate to **Settings** -> **API Keys**
3. Generate a new API key

### Include your API key in all requests:
```
Header: Authorization: Bearer YOUR_API_KEY
```

## 3. Base URL
All API requests should be made to:
```
https://api.lianflow.com/v1
```

## 4. API Endpoints

### 4.1 Create Payment
**POST** `/payment/create`

**Request Headers:**
```json
{
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
    "amount": float,            // Payment amount
    "sender_address": "string", // Sender's wallet address
    "data": "string",          // Additional metadata (e.g., email)
    "webhook_url": "string"    // Webhook URL for notifications
}
```

**Response:**
```json
{
    "payment_id": "uuid",
    "merchant_address": "string"
}
```

### 4.2 Get Payment Details
**GET** `/payment/{paymentId}`

**Response:**
```json
{
    "payment_id": "string",
    "business_name": "string",
    "business_id": "string",
    "gas_amount": float,
    "total_amount": float
}
```

### 4.3 Check Payment Status
**GET** `/payment/status/{paymentId}`

**Response:**
```json
{
    "payment_id": "string",
    "status": "string",
    "transaction_hash": "string"
}
```

### 4.4 Get Transaction Details
**GET** `/transaction/{transactionId}`

**Response:**
```json
{
    "transaction_id": "string",
    "payment_id": "string",
    "from_address": "string",
    "to_address": "string",
    "amount": float,
    "gas_fee": float,
    "status": "string",
    "block_number": integer,
    "transaction_hash": "string"
}
```

## 5. Webhook Integration
When creating a payment, specify a webhook URL to receive real-time payment updates.

**Webhook Payload:**
```json
{
    "receipt": object,
    "email": "string",
    "payment_id": "string",
    "status": "string",
    "amount": float,
    "sender": "string",
    "receiver": "string",
    "transaction_hash": "string",
    "user_id": "string",
    "gas_fee": float
}
```

## 6. Error Handling
### Common HTTP Status Codes:
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized (Invalid API key)
- `403`: Forbidden (Insufficient permissions)
- `404`: Not Found
- `500`: Internal Server Error

## 7. Code Examples

### Python Example:
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.lianflow.com/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Create payment
payment_data = {
    "amount": 100.0,
    "sender_address": "sender_wallet_address",
    "data": "customer@email.com",
    "webhook_url": "https://your-website.com/webhook"
}

response = requests.post(
    f"{BASE_URL}/payment/create",
    headers=headers,
    json=payment_data
)

print(response.json())
```

### JavaScript Example:
```javascript
const API_KEY = 'your_api_key';
const BASE_URL = 'https://api.lianflow.com/v1';

const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
};

// Create payment
const paymentData = {
    amount: 100.0,
    sender_address: 'sender_wallet_address',
    data: 'customer@email.com',
    webhook_url: 'https://your-website.com/webhook'
};

fetch(`${BASE_URL}/payment/create`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify(paymentData)
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

## 8. Support
For technical support:
- **Email**: support@lianflow.com
- **Documentation**: [LianFlow Docs](https://docs.lianflow.com)
- **API Status**: [LianFlow Status](https://status.lianflow.com)

### Best Practices:
1. Always store API keys securely.
2. Implement proper error handling.
3. Test thoroughly in sandbox environment before going live.
4. Monitor webhook endpoints for reliability.
5. Keep your integration up to date.

### Rate Limits:
- 1000 requests per minute per API key
- Webhook timeout: 10 seconds

For additional support or feature requests, please contact our support team.