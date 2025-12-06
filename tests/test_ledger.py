import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_account(client: AsyncClient):
    response = await client.post(
        "/api/v1/accounts/", json={"name": "Test User", "currency": "USD"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test User"
    assert float(data["balance"]) == 0.0


@pytest.mark.asyncio
async def test_deposit_withdrawal_flow(client: AsyncClient):
    # 1. Create Account
    acc_res = await client.post(
        "/api/v1/accounts/", json={"name": "Flow User", "currency": "USD"}
    )
    account_id = acc_res.json()["id"]

    # 2. Deposit $100
    dep_res = await client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_id,
            "type": "DEPOSIT",
            "amount": 100,
            "reference": "Init Deposit",
        },
    )
    assert dep_res.status_code == 201

    # 3. Check Balance
    bal_res = await client.get(f"/api/v1/accounts/{account_id}")
    assert float(bal_res.json()["balance"]) == 100.0

    # 4. Withdraw $40
    with_res = await client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_id,
            "type": "WITHDRAWAL",
            "amount": 40,
            "reference": "ATM Withdraw",
        },
    )
    assert with_res.status_code == 201

    # 5. Check Balance
    bal_res = await client.get(f"/api/v1/accounts/{account_id}")
    assert float(bal_res.json()["balance"]) == 60.0


@pytest.mark.asyncio
async def test_race_condition_withdrawal(client: AsyncClient):
    """
    Simulate 10 concurrent withdrawals of $20 from an account with $100.
    Only 5 should succeed. Balance should be 0.
    """
    # 1. Create Account
    acc_res = await client.post(
        "/api/v1/accounts/", json={"name": "Race User", "currency": "USD"}
    )
    account_id = acc_res.json()["id"]

    # 2. Deposit $100
    await client.post(
        "/api/v1/transactions/",
        json={"account_id": account_id, "type": "DEPOSIT", "amount": 100},
    )

    # 3. Fire 10 concurrent requests
    async def withdraw():
        return await client.post(
            "/api/v1/transactions/",
            json={"account_id": account_id, "type": "WITHDRAWAL", "amount": 20},
        )

    tasks = [withdraw() for _ in range(10)]
    responses = await asyncio.gather(*tasks)

    # 4. Count successes
    success_count = sum(1 for r in responses if r.status_code == 201)
    fail_count = sum(1 for r in responses if r.status_code == 400)

    print(f"Successes: {success_count}, Failures: {fail_count}")

    # 5. Assertions
    assert success_count == 5
    assert fail_count == 5

    # 6. Verify Final Balance
    bal_res = await client.get(f"/api/v1/accounts/{account_id}")
    assert float(bal_res.json()["balance"]) == 0.0


@pytest.mark.asyncio
async def test_idempotency(client: AsyncClient):
    # 1. Create Account
    acc_res = await client.post(
        "/api/v1/accounts/", json={"name": "Idem User", "currency": "USD"}
    )
    account_id = acc_res.json()["id"]

    # 2. Deposit $100
    await client.post(
        "/api/v1/transactions/",
        json={"account_id": account_id, "type": "DEPOSIT", "amount": 100},
    )

    # 3. Send Transfer Request with Key "key1"
    payload = {
        "account_id": account_id,
        "type": "WITHDRAWAL",
        "amount": 50,
        "reference": "First Try",
    }
    headers = {"Idempotency-Key": "key1"}

    res1 = await client.post("/api/v1/transactions/", json=payload, headers=headers)
    assert res1.status_code == 201
    tx_id1 = res1.json()["id"]

    # 4. Send SAME Request with SAME Key "key1"
    res2 = await client.post("/api/v1/transactions/", json=payload, headers=headers)
    assert res2.status_code == 201
    tx_id2 = res2.json()["id"]

    # 5. Assertions
    assert tx_id1 == tx_id2  # Should return exact same transaction ID

    # 6. Verify Balance (Should be 50, not 0)
    bal_res = await client.get(f"/api/v1/accounts/{account_id}")
    assert float(bal_res.json()["balance"]) == 50.0
