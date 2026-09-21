# 💻 About Project #13

[Complete Guide | Run this project on your computer](https://github.com/danialafjeh/Run-My-Projects-Locally)<br>
Projects are numbered in development order. Higher numbers represent newer projects that introduce new backend tools, concepts, and increasing levels of complexity throughout my learning journey.


# Payment System API

A backend payment system API built with Django REST Framework, designed to simulate the payment infrastructure of an online store with an internal customer wallet.

The project provides a complete backend workflow for user registration, wallet management, deposits, payments, transactions, refunds, authentication, idempotency, rate limiting, API documentation, and administrative read-only access.

The payment provider is intentionally implemented as a mock gateway. Therefore, this project does not connect to a real bank or payment provider and does not process real money.

---

## Overview

This project represents the backend of an online store that provides customers with an internal wallet.

Customers can:

* Create an account
* Authenticate using JWT
* Have an internal wallet automatically created for their account
* Deposit funds into their wallet
* Create payments
* Process payments using their wallet balance
* View their payment history
* View their transaction history
* Request partial or full refunds
* Receive refunded amounts back into their wallet

The system also maintains a transaction ledger for financial operations and uses Redis to provide idempotency and API rate limiting.

The architecture is designed around clear separation between HTTP/API handling, validation, business logic, and database persistence.

---

## Main Features

### Authentication

* User registration
* JWT authentication
* Access and refresh tokens using Simple JWT
* Protected API endpoints
* Admin-only endpoints using Django's built-in user permissions

### Wallet System

Each registered user automatically receives one internal wallet.

The wallet:

* Belongs to exactly one user
* Starts with a zero balance
* Supports deposits
* Supports balance increases from successful refunds
* Supports balance decreases after successful payments
* Uses database row locking during financial operations to prevent concurrent balance updates

### Payment Processing

The payment system supports:

* Payment creation
* Payment processing
* Payment status management
* Unique UUID tracking codes
* Payment descriptions
* User-specific payment history
* Insufficient balance validation
* Transaction creation for each payment

Payment states include:

```text
pending
processing
success
failed
refunded
```

A payment must first be created in the `pending` state before it can be processed.

Only pending payments can be processed.

---

## Refund System

The API supports both partial and full refunds.

Refunds are independent records associated with their original payment.

The system validates:

* The original payment must be successful
* The refund amount cannot exceed the remaining refundable amount
* Multiple partial refunds are supported
* The total successful refunds cannot exceed the original payment amount
* A fully refunded payment is marked as `refunded`
* Successful refunds increase the user's wallet balance

Refund states include:

```text
pending
processing
success
failed
```

Every refund also creates a corresponding transaction ledger entry.

---

## Transaction Ledger

The `Transaction` model acts as the financial ledger of the system.

It records:

* Payments
* Refunds
* Deposits

Supported transaction types:

```text
payment
refund
deposit
```

Transaction statuses include:

```text
pending
completed
failed
```

Deposits and refunds do not directly create money. They represent successful external funding or refund operations through the mock payment gateway.

For example:

```text
Deposit
    ↓
Mock Payment Gateway
    ↓
Successful external funding simulation
    ↓
Wallet balance increases
    ↓
Deposit transaction becomes completed
```

Similarly:

```text
Payment
    ↓
Wallet balance decreases
    ↓
Payment transaction becomes completed
```

And:

```text
Refund
    ↓
Mock Payment Gateway
    ↓
Wallet balance increases
    ↓
Refund transaction becomes completed
```

---

## Idempotency

The API implements idempotency for operations where duplicate requests could result in duplicate financial actions.

The following operations use idempotency keys:

* Payment creation
* Refund creation
* Wallet deposits

Clients must provide an `Idempotency-Key` header for these operations.

Example:

```http
Idempotency-Key: 8f9f4e2d-1b6a-4d6f-9e22-example
```

Redis is used to store the idempotency state.

The flow is:

```text
Client Request
      |
      v
Idempotency-Key
      |
      v
Redis
      |
      +---- processing
      |
      +---- final response
```

If the same key is submitted again, the API prevents the operation from being created twice and can return the previously stored result.

The idempotency key is scoped by both the user and operation type, preventing collisions between different users or different financial operations.

---

## Rate Limiting

The API uses Django REST Framework's built-in throttling system.

The current configuration uses:

```text
UserRateThrottle
5 requests / minute
```

This limit is intentionally configured at a low value during development and testing.

Redis is used as the backend for Django's cache system, allowing throttling data to be stored outside the Django application process.

---

## Concurrency and Financial Consistency

Financial operations require special attention to concurrent requests.

The project uses:

* `transaction.atomic()`
* `select_for_update()`
* PostgreSQL transactions
* Row-level locking

For example, when processing a payment, the user's wallet is locked before checking and changing its balance.

Conceptually:

```text
Request A
   |
   +--> Lock Wallet
   |
   +--> Check Balance
   |
   +--> Decrease Balance
   |
   +--> Commit


Request B
   |
   +--> Wait for Wallet Lock
   |
   +--> Re-check Balance
   |
   +--> Continue
```

This helps prevent race conditions where multiple simultaneous requests could incorrectly modify the same wallet balance.

PostgreSQL acts as the source of truth for financial data.

---

## Mock Payment Gateway

The project contains a `MockPaymentGateway` service that simulates communication with an external payment provider.

It currently supports:

```text
process_payment()
process_refund()
process_deposit()
```

The gateway is intentionally mocked and does not communicate with a real banking system, payment processor, or financial institution.

This design allows the rest of the payment architecture to be developed without requiring external credentials or real financial transactions.

A real payment provider could later replace the mock implementation while keeping the business logic separated from the external gateway layer.

---

## Architecture

The project follows a service-oriented backend structure.

The main responsibilities are separated as follows:

```text
Client
  |
  v
DRF View / ViewSet
  |
  v
Serializer
  |
  v
Service Layer
  |
  +------> Payment Gateway
  |
  +------> Wallet Service
  |
  +------> Idempotency Service
  |
  v
Django ORM
  |
  v
PostgreSQL
```

Redis is used alongside the application for:

```text
Idempotency
Rate Limiting
Django Cache
```

---

## Service Layer

Business logic is separated into dedicated services.

### PaymentService

Responsible for payment creation and processing.

Responsibilities include:

* Creating payments
* Creating payment transactions
* Locking payments during processing
* Locking wallets
* Checking wallet balance
* Calling the payment gateway
* Updating payment status
* Updating transaction status

### RefundService

Responsible for refund processing.

Responsibilities include:

* Validating refundable payments
* Calculating the already refunded amount
* Preventing excessive refunds
* Creating refund records
* Creating refund transactions
* Calling the mock gateway
* Returning refunded funds to the wallet
* Marking fully refunded payments

### WalletService

Responsible for wallet operations.

Responsibilities include:

* Retrieving locked wallets
* Increasing wallet balances
* Decreasing wallet balances
* Processing wallet deposits

### IdempotencyService

Responsible for:

* Generating operation-specific Redis keys
* Claiming idempotency keys
* Detecting previously processed requests
* Storing final responses

---

## Database Models

The project contains four main models.

### User

Django's built-in `User` model is used for authentication.

No custom user model is required.

### Wallet

Represents the internal wallet belonging to a user.

Relationship:

```text
User 1 ───── 1 Wallet
```

Important fields include:

* `user`
* `balance`
* `created_at`
* `updated_at`

### Payment

Represents a payment initiated by a user.

Important fields include:

* `user`
* `amount`
* `status`
* `tracking_code`
* `description`
* `created_at`
* `updated_at`

The `tracking_code` is a unique UUID and can be used as a public payment reference.

### Transaction

Represents an entry in the financial ledger.

Important fields include:

* `user`
* `payment`
* `amount`
* `transaction_type`
* `status`
* `created_at`

A transaction can represent:

```text
Payment
Refund
Deposit
```

### Refund

Represents a refund associated with a payment.

Important fields include:

* `payment`
* `amount`
* `status`
* `reason`
* `created_at`
* `updated_at`

Relationships:

```text
User
 |
 +---- Wallet
 |
 +---- Payments
 |
 +---- Transactions

Payment
 |
 +---- Transactions
 |
 +---- Refunds
```

---

## API Structure

The API is implemented using Django REST Framework.

Different DRF components are used according to the responsibility of each endpoint.

### ModelViewSet

Used where standard resource operations are appropriate.

Examples include payment and transaction resources.

### ReadOnlyModelViewSet

Used for administrative read-only resources.

### APIView

Used for operations that represent specific business actions rather than standard CRUD operations.

Examples include:

* User registration
* Wallet deposits
* Refund operations

---

## Main API Operations

### Authentication

User registration is available through the registration endpoint.

A newly registered user automatically receives an empty wallet.

JWT authentication is provided through Simple JWT.

---

### Payments

Payment operations include:

```text
GET     Payment list
GET     Payment detail
POST    Create payment
POST    Process payment
```

Payment data is scoped to the authenticated user for normal user-facing endpoints.

A payment requires an `Idempotency-Key` when it is created.

---

### Wallet Deposits

The wallet deposit endpoint allows users to add funds to their internal wallet through the simulated external payment flow.

```text
POST /api/wallet/deposit/
```

The deposit:

1. Validates the amount
2. Creates a pending deposit transaction
3. Calls the mock payment gateway
4. Increases the wallet balance after success
5. Marks the transaction as completed

---

### Refunds

Refunds are created against an existing successful payment.

The system supports:

```text
Partial Refund
Full Refund
Multiple Partial Refunds
```

A refund cannot exceed the remaining refundable amount.

---

### Transactions

Authenticated users can retrieve their transaction history.

Transactions provide a unified view of:

```text
Deposits
Payments
Refunds
```

This provides a simple financial ledger for the user's activity.

---

## Administrative API

The project includes separate read-only administrative endpoints.

Available resources include:

```text
/api/admin/users/
/api/admin/payments/
/api/admin/transactions/
```

These endpoints are protected with Django REST Framework's `IsAdminUser` permission.

Administrators can:

* List users
* Search users
* Retrieve individual users
* List payments
* Search payments by username
* Retrieve individual payments
* List transactions
* Search transactions by username
* Retrieve individual transactions

The administrative API is intentionally read-only.

---

## Pagination

DRF pagination is enabled for list endpoints to prevent large collections from being returned in a single response.

This applies to resources such as:

* Payments
* Transactions
* Administrative lists

---

## API Documentation

The API is documented using `drf-spectacular`.

Available documentation endpoints:

```text
/api/schema/
/api/docs/
/api/redoc/
```

The project provides:

* OpenAPI schema
* Swagger UI
* ReDoc

ReDoc can be used as a convenient reference for exploring the available endpoints, request parameters, authentication requirements, and response structures.

---

## Technology Stack

### Backend

* Python
* Django
* Django REST Framework

### Authentication

* Simple JWT
* Django Authentication

### Database

* PostgreSQL
* Django ORM

### Cache and Infrastructure

* Redis
* django-redis

### API Documentation

* drf-spectacular
* OpenAPI
* Swagger UI
* ReDoc

### Containerization

* Docker

---

## Dockerization

The project is fully containerized using Docker Compose.

The application is separated into three main services:

```text
Django
PostgreSQL
Redis
```

Architecture:

```text
                 ┌─────────────────────┐
                 │       Client        │
                 └──────────┬──────────┘
                            │
                            v
                 ┌─────────────────────┐
                 │   Django / DRF      │
                 │   Payment API       │
                 └──────┬───────┬──────┘
                        │       │
              ┌─────────┘       └─────────┐
              v                           v
     ┌─────────────────┐         ┌─────────────────┐
     │   PostgreSQL    │         │      Redis      │
     │   Source of     │         │  Idempotency    │
     │     Truth       │         │  Rate Limiting  │
     └─────────────────┘         └─────────────────┘
```

The Django container automatically runs database migrations when the application starts.

The Docker setup also uses health checks for PostgreSQL and Redis, allowing the Django service to wait for the required infrastructure services to become healthy.

The project currently uses Django's development server inside the container and does not include Gunicorn or Nginx.

This keeps the Docker setup focused on the application architecture without introducing unnecessary deployment complexity.

---

## Docker Services

### Django

Runs the Django REST Framework application.

Responsibilities:

* API endpoints
* Authentication
* Business logic
* Database access
* Redis integration
* API documentation

### PostgreSQL

Stores persistent application data.

PostgreSQL is the source of truth for:

* Users
* Wallets
* Payments
* Transactions
* Refunds

### Redis

Used for:

* Idempotency
* Rate limiting
* Django caching infrastructure

Redis is not used as the source of truth for financial records.

---

## Configuration

The Django application reads infrastructure configuration through environment variables using Python's `os.getenv()`.

Examples include:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
REDIS_URL
```

This keeps infrastructure-specific configuration outside the Django source code and allows the same application to be configured differently in different environments.

For local development, Docker Compose provides the required environment variables.

For production-style deployments, these values can be supplied through environment-specific configuration or an `.env` file without changing the application code.

---

## Project Structure

```text
payment-system-api/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── api/
│   ├── migrations/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── payment_service.py
│   │   ├── payment_gateway.py
│   │   ├── idempotency_service.py
│   │   ├── wallet_service.py
│   │   └── refund_service.py
│   │
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── tests.py
│
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── .dockerignore
└── .gitignore
```

---

## Running the Project with Docker

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/payment-system-api.git
cd payment-system-api
```

Build and start the services:

```bash
docker compose up --build
```

After the containers are running, the API is available at:

```text
http://localhost:8000/
```

API documentation:

```text
http://localhost:8000/api/docs/
```

ReDoc:

```text
http://localhost:8000/api/redoc/
```

OpenAPI schema:

```text
http://localhost:8000/api/schema/
```

To stop the services:

```bash
docker compose down
```

To stop the services while keeping the PostgreSQL volume:

```bash
docker compose down
```

The PostgreSQL data is stored in a Docker volume so that container recreation does not automatically remove the database data.

---

## Example Financial Flow

A typical customer flow can be represented as:

```text
1. User Registration
        |
        v
2. Wallet Created
   Balance = 0
        |
        v
3. Wallet Deposit
        |
        v
4. Mock Payment Gateway
        |
        v
5. Wallet Balance Increased
        |
        v
6. Create Payment
        |
        v
7. Process Payment
        |
        v
8. Wallet Balance Decreased
        |
        v
9. Payment Transaction Completed
        |
        v
10. Refund
        |
        v
11. Wallet Balance Increased
        |
        v
12. Refund Transaction Completed
```

For example, a customer may deposit funds into their wallet, use part of the balance to make a payment, and later receive a partial refund.

All of these operations are represented in the transaction ledger.

---

## Design Principles

The project follows several backend design principles.

### Separation of Responsibilities

Serializers are primarily responsible for validation and serialization.

Views handle HTTP-level responsibilities and orchestration.

Services contain business logic.

Models and the Django ORM handle persistence.

This keeps complex financial logic out of serializers and views.

### Database as the Source of Truth

Financial information is stored in PostgreSQL.

Redis is used for temporary operational data such as:

* Idempotency state
* Cached responses
* Rate limiting information

Redis is not used as the authoritative store for wallet balances or transaction records.

### Explicit Business Rules

Financial operations validate their state before modifying data.

Examples include:

* Only pending payments can be processed
* Only successful payments can be refunded
* Refunds cannot exceed the remaining refundable amount
* Wallet balances cannot be reduced below the required payment amount
* Duplicate idempotent requests cannot create duplicate financial operations

### Transactional Integrity

Financial operations are wrapped in database transactions and use row-level locking where concurrent modifications could occur.

This provides stronger consistency for wallet and payment operations.

---

## Security Considerations

The project includes several backend security and reliability mechanisms:

* JWT authentication
* Authenticated user-specific data access
* Admin-only administrative APIs
* PostgreSQL transactions
* Row-level locking
* Idempotency keys
* Rate limiting
* Unique UUID payment tracking codes
* Protected foreign-key relationships
* Environment-based infrastructure configuration

This project is an educational and portfolio implementation and is not intended to process real financial transactions without additional security, compliance, auditing, monitoring, fraud prevention, and payment-provider integration.

---

## Project Purpose

This project was developed as a backend portfolio project to demonstrate practical experience with:

* Django
* Django REST Framework
* PostgreSQL
* Redis
* JWT authentication
* Service-layer architecture (Main goal)
* Financial transaction workflows (Main goal)
* Database transactions (Main goal)
* Row-level locking (Main goal)
* Idempotent APIs (Main goal)
* Rate limiting (Main goal)
* API documentation
* Docker

The main goal is to demonstrate how a realistic backend payment workflow can be structured and implemented while keeping external payment processing isolated behind a gateway abstraction.

---

## Disclaimer

This is a simulated payment system for educational and portfolio purposes.

It does not process real money, communicate with real banks, or integrate with a real payment provider.

The payment gateway is mocked, and wallet balances represent application-level balances within the simulated store environment.
