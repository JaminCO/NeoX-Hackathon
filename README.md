# NeoX Crypto Payment Gateway

A FastAPI-based cryptocurrency payment gateway that allows businesses to accept crypto payments using the NeoX blockchain.

## Features

- Business account creation and management
- Wallet creation and import functionality
- Payment processing and transaction monitoring
- Real-time payment status updates via WebSocket
- Secure API key authentication
- Webhook notifications for payment status updates

## Tech Stack

- **FastAPI** (Python web framework)
- **SQLAlchemy** (ORM)
- **Web3.py** (Blockchain interaction)
- **PostgreSQL/SQLite** (Database)

## API Routes

### Authentication Routes

#### `POST /users/signup`
Create a new business account.
- **Request Body**:
  ```json
  {
    "business_name": "string",
    "email": "string",
    "password": "string",
  }
  ```

- **Returns**: User ID and API key

#### `POST /users/token`
Login using username/password.
- **Request Body**:
  ```json
  {
    "email": "string",
    "password": "string",
  }
  ```
- **Returns**: JWT access token

### API Routes (Requires API Key Authentication)

All API routes require an API key to be passed in the header:

```
Authorization: Bearer YOUR_API_KEY
```

You can obtain your API key from:
1. Initial signup response
2. Dashboard settings
3. Using the regenerate API key endpoint (`POST /users/regenerate-api-key`)

#### Payment Routes

1. **Create Payment**

   `POST /api/v1/payment/create`

   Initiates a new payment request.
   - **Required fields**:
     - `amount`: float
     - `data`: string (metadata)
     - `sender_address`: string
     - `business_id`: string
     - `webhook`: string (URL for payment notifications)
   - **Returns**: Payment ID and merchant address

2. **Get Payment Details**

   `GET /api/v1/payment/{paymentId}`

   Retrieve details of a specific payment.
   - **Returns**: Payment details including status and amounts

3. **Check Payment Status**

   `GET /api/v1/payment/status/{paymentId}`

   Get the current status of a payment.
   - **Returns**: Payment status and transaction hash

#### Transaction Routes

1. **Get Transaction Details**

   `GET /api/v1/transaction/{transactionId}`

   Retrieve details of a specific transaction.

2. **Get Wallet Transactions**

   `GET /api/v1/transaction/to/{wallet_address}`

   Get all transactions for a specific wallet address.

## Webhook Notifications

The system sends webhook notifications to the URL specified during payment creation. The webhook payload includes:
- Payment details
- Transaction status
- Transaction hash
- Amount information
- Sender and receiver addresses

## Security

- API authentication using API keys
- JWT-based session management
- Password hashing using bcrypt
- CORS protection
- Rate limiting (if configured)

## Project Structure

```
project/
├── app.py           # Main FastAPI application
├── api.py           # API routes and handlers
├── models.py        # Database models
├── schema.py        # Pydantic models for request/response
├── database.py      # Database configuration
├── xenon.py         # Blockchain interaction utilities
├── monitor.py       # Transaction monitoring
└── README.md        # Project documentation
```

### File Descriptions

#### `app.py`
Main application file containing:
- FastAPI app configuration
- CORS middleware setup
- Authentication routes
- Web interface routes
- WebSocket handling

#### `api.py`
API routes for external integrations:
- Payment creation and management
- Transaction monitoring
- Webhook notifications
- API key authentication

#### `models.py`
SQLAlchemy models for:
- Business accounts
- Wallets
- Payments
- Transactions
- Analytics

#### `schema.py`
Pydantic models for:
- Request validation
- Response serialization
- Data transfer objects

#### `database.py`
Database configuration:
- SQLAlchemy engine setup
- Session management
- Base model configuration

#### `xenon.py`
Blockchain utilities:
- Wallet creation/import
- Balance checking
- Transaction handling
- Gas price conversion

#### `monitor.py`
Transaction monitoring:
- Real-time transaction tracking
- Payment verification
- Block confirmation monitoring

## Development

1. The project uses SQLite by default. For production, configure PostgreSQL in `database.py`.
2. Update CORS settings in `app.py` for production.
3. Set up proper environment variables.
4. Implement proper error handling and logging.

## Environment Variables

Required environment variables:
- `SECRET_KEY`: JWT secret key
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)
- `RPC_URL`: NeoX blockchain RPC endpoint
- `WS_URL`: WebSocket endpoint for blockchain events