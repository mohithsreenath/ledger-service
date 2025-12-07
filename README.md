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

### Database Choice: PostgreSQL
*   **Why**: Selected for strict **ACID compliance** and **Row-Level Locking** capabilities.
*   **Schema**: Implements **Double-Entry Bookkeeping**.
    *   `LedgerEntry`: Immutable record of every credit/debit.
    *   `Account.balance`: Updated via transaction but protected by constraints (`CHECK balance >= 0`).

### Concurrency Strategy: Pessimistic Locking
*   **Mechanism**: Uses `SELECT ... FOR UPDATE` to lock account rows during a transaction.
*   **Deadlock Prevention**: Resource ordering (sorting Account IDs) is enforced before locking.
*   **Result**: Validated to strictly prevent double-spending and race conditions.


## 📁 Key Deliverables
*   **Language**: Python 3.11 / FastAPI
*   **Type Safety**: Strict Pydantic models (Input/Output validation).
*   **Testing**: Full integration coverage for financial correctness.
