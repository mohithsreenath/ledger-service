# Transactional Ledger Service

A strict, ACID-compliant ledger API built with **Python (FastAPI)** and **PostgreSQL**.

## 🛠️ Quick Start (Developer Mode)

### 1. Run Application
Start the API and Database (Postgres 15). The `.env` is included for zero-config startup.
```bash
docker-compose up --build
```
*   **API**: `http://localhost:8000/api/v1`
*   **Swagger Docs**: `http://localhost:8000/docs`

### 2. Run Tests
Execute the integration suite, including race condition verification (simulates 10 concurrent requests).
```bash
docker-compose run --rm app pytest
```

---

## 🏛️ Architecture & Design Decisions

### 1. Database Choice: PostgreSQL
*   **Why SQL over NoSQL?**: Financial data requires **ACID** compliance (Atomicity, Consistency, Isolation, Durability).
*   **PostgreSQL**: Chosen for its robust transaction support (Row-Level Locking) and `DECIMAL` type precision, which effectively eliminates floating-point rounding errors common in MongoDB or simple float types.
*   **Schema**: A **Double-Entry Bookkeeping** model was implemented. Every transaction creates at least two immutable `LedgerEntry` records (Debit/Credit). This ensures that the sum of all entries is always zero, providing a built-in audit trail and integrity check.

### 2. Concurrency Strategy
*   **Problem**: Race conditions (e.g., two concurrent withdrawals of $100 from a $150 balance).
*   **Solution**: **Pessimistic Locking** (`SELECT ... FOR UPDATE`).
*   **Implementation**: When processing a transaction, we explicitly lock the involved Account rows in the database.
*   **Deadlock Prevention**: We enforced a strict **Resource Ordering** rule: always lock Account IDs in ascending order (e.g., Lock ID A, then ID B). This makes deadlocks mathematically impossible in standard transfers.

### 3. Scaling Trade-offs (Roadmap to 1 Million TPS)
*   **Current Limit**: The current Pessimistic Locking strategy scales reliably to ~1,000 TPS (Transactions Per Second) but creates a bottleneck on "hot accounts" (e.g., a massive merchant account receiving thousands of payments at once).
*   **Future 1M TPS Design**:
    *   **Event Sourcing**: Switch to an append-only log (like Apache Kafka) for ingestion.
    *   **CQRS**: Separate the Write model (High speed ingestion) from the Read model (Balances).
    *   **Sharding**: Partition the database by Account ID to distribute load horizontally.
    *   **Trade-off**: We would move from Strong Consistency (Immediate Balance Update) to **Eventual Consistency** (Balance updates a few milliseconds later) to achieve this massive throughput.

## 📁 Key Deliverables
*   **Language**: Python 3.11 / FastAPI
*   **Type Safety**: Strict Pydantic models (Input/Output validation).
*   **Testing**: Full integration coverage for financial correctness.
