# Transactional Ledger Service

## Overview
A simplified internal ledger system built with **Python (FastAPI)** and **PostgreSQL**. It handles money movement between accounts with strict financial accuracy, supporting high concurrency and failure conditions.

## Architecture

### Technology Stack
- **Language**: Python 3.11+ (FastAPI)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy (Async)
- **Containerization**: Docker & Docker Compose

### Database Choice: PostgreSQL
We chose PostgreSQL over MongoDB for the following reasons:
1.  **ACID Transactions**: Financial data requires strict atomicity and consistency. Postgres provides robust transaction support.
2.  **Row-Level Locking**: To handle race conditions (double-spending), we use `SELECT ... FOR UPDATE` to lock specific account rows during a transaction.
3.  **Data Integrity**: Strong typing and constraints ensure that data remains valid (e.g., foreign keys, check constraints).

### Schema Design: Double-Entry Bookkeeping
We implement a **Double-Entry Bookkeeping** system to ensure auditability and accuracy.
- **`accounts`**: Stores the current balance (cached for performance) and account details.
- **`ledger_entries`**: The immutable source of truth. Every transaction creates at least two entries (one debit, one credit).
    - **Deposit**: Credit User Account, Debit System Cash Account.
    - **Withdrawal**: Debit User Account, Credit System Cash Account.
    - **Transfer**: Debit Sender, Credit Receiver.
- **`transactions`**: Groups ledger entries into a logical operation and handles **Idempotency**.

### Concurrency Strategy
To prevent race conditions (e.g., two simultaneous withdrawals of $100 from an account with $100):
- We use **Pessimistic Locking** (`SELECT FOR UPDATE`) on the `accounts` table within a database transaction.
- This ensures that once a transaction reads an account's balance to check for sufficient funds, no other transaction can modify that account until the first one commits or rolls back.
- We sort account IDs before locking to prevent **Deadlocks**.

### Idempotency
- Clients must provide a unique `Idempotency-Key` header.
- The system checks the `transactions` table for this key.
- If found, it returns the previous result without re-processing.

## Trade-offs & Scaling
If this system had to handle **1 million transactions per second**:
1.  **Database Partitioning/Sharding**: A single Postgres instance cannot write 1M TPS. We would shard the database by Account ID.
2.  **Event Sourcing**: Instead of locking, we could use an event log (Kafka) and process transactions asynchronously. This trades immediate consistency for high throughput (Eventual Consistency).
3.  **Caching**: Use Redis for read-heavy balance checks (with cache invalidation strategies).

## Running the Project
```bash
docker-compose up --build
```
The API will be available at `http://localhost:8000`.
Docs: `http://localhost:8000/docs`
