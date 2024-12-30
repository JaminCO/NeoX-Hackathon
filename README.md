# LianFlow Crypto Payment Gateway

LianFlow is designed to simplify crypto payment processing for businesses operating on the NEO X blockchain. The solution empowers businesses to accept cryptocurrency payments for their products and services while offering an easy-to-integrate system for existing codebases and platforms. By streamlining the integration process, the platform reduces the technical barriers that often deter businesses from adopting blockchain-based payments..

## Key Features

- **Business Account Management**: Streamlined processes for creating and managing business accounts.
- **Wallet Operations**: Easy wallet creation and import for secure and efficient transactions.
- **Seamless Payment Processing**: Efficient handling of payments with real-time transaction monitoring.
- **Instant Payment Updates**: Real-time status updates via WebSocket for immediate insights.
- **Secure API Authentication**: Protect your transactions with robust API key authentication.
- **Proactive Webhook Notifications**: Stay informed with instant notifications on payment status changes.

## Technology Stack

- **FastAPI**: A modern, high-performance web framework for building APIs with Python.
- **SQLAlchemy**: A powerful ORM for database management and operations.
- **Web3.py**: A comprehensive library for interacting with the blockchain.
- **PostgreSQL/SQLite**: Reliable databases for storing and managing data.

## API INTEGRATION

For a more Detailed Documentation for Integration check [LianFlow Documentaion](/Documentation.md)


## API Endpoints

All API routes require an API key to be passed in the header:

```
Authorization: Bearer YOUR_API_KEY
```

You can obtain your API key from:
1. Settings page -> API Keys tab

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