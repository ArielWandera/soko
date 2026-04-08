"""
Edge case and new-feature integration tests.
Run after test_full_flow.py — depends on the same session fixtures.
"""
import httpx
import pytest
from helpers import BASE_URLS, auth_headers, register_and_login


# ── Token refresh ──────────────────────────────────────────────────────

def test_token_refresh(farmer_token):
    resp = httpx.post(
        f"{BASE_URLS['auth']}/auth/refresh",
        headers=auth_headers(farmer_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    new_token = body["access_token"]
    # New token must be usable
    me = httpx.get(f"{BASE_URLS['auth']}/auth/me", headers=auth_headers(new_token))
    assert me.status_code == 200


def test_refresh_rejects_bad_token():
    resp = httpx.post(
        f"{BASE_URLS['auth']}/auth/refresh",
        headers={"Authorization": "Bearer fake.token.here"},
    )
    assert resp.status_code == 401


# ── Farmer public list ─────────────────────────────────────────────────

def test_farmer_public_list(farmer_profile):
    resp = httpx.get(f"{BASE_URLS['farmer']}/farmers/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    farmer_ids = [f["id"] for f in body["results"]]
    assert farmer_profile["id"] in farmer_ids


def test_farmer_by_user_id(farmer_profile):
    user_id = farmer_profile["user_id"]
    resp = httpx.get(f"{BASE_URLS['farmer']}/farmers/by-user/{user_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == farmer_profile["id"]


# ── Produce listing enrichment ─────────────────────────────────────────

def test_produce_listing_has_farmer_name(produce_listing):
    pid = produce_listing["id"]
    resp = httpx.get(f"{BASE_URLS['produce']}/produce/{pid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["farmer_name"] is not None
    assert len(body["farmer_name"]) > 0


def test_produce_listing_has_rating_fields(produce_listing):
    pid = produce_listing["id"]
    resp = httpx.get(f"{BASE_URLS['produce']}/produce/{pid}")
    assert resp.status_code == 200
    body = resp.json()
    assert "avg_rating" in body
    assert "review_count" in body
    assert body["avg_rating"] >= 0.0
    assert body["review_count"] >= 0


def test_price_predictions_endpoint():
    resp = httpx.get(f"{BASE_URLS['produce']}/produce/prices/predictions")
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body


def test_produce_new_categories(farmer_token):
    """cash_crops, dairy, herbs should all be accepted."""
    for category in ("cash_crops", "dairy", "herbs"):
        resp = httpx.post(
            f"{BASE_URLS['produce']}/produce/",
            json={
                "name": f"Test {category}",
                "category": category,
                "quantity": 10.0,
                "price_per_unit": 1000.0,
                "district": "Kampala",
                "unit": "kg",
            },
            headers=auth_headers(farmer_token),
        )
        assert resp.status_code == 201, f"Category '{category}' rejected: {resp.text}"


# ── Input validation ───────────────────────────────────────────────────

def test_produce_rejects_zero_quantity(farmer_token):
    resp = httpx.post(
        f"{BASE_URLS['produce']}/produce/",
        json={"name": "Bad Listing", "category": "grains", "quantity": 0, "price_per_unit": 500.0, "district": "Kampala"},
        headers=auth_headers(farmer_token),
    )
    assert resp.status_code == 422


def test_produce_rejects_zero_price(farmer_token):
    resp = httpx.post(
        f"{BASE_URLS['produce']}/produce/",
        json={"name": "Bad Listing", "category": "grains", "quantity": 10.0, "price_per_unit": 0, "district": "Kampala"},
        headers=auth_headers(farmer_token),
    )
    assert resp.status_code == 422


def test_order_rejects_zero_quantity(buyer_token, produce_listing):
    resp = httpx.post(
        f"{BASE_URLS['buyer']}/orders/",
        json={"produce_id": produce_listing["id"], "quantity_kg": 0},
        headers=auth_headers(buyer_token),
    )
    assert resp.status_code == 422


# ── Farmer order management ────────────────────────────────────────────

def test_farmer_can_see_orders(farmer_token, placed_order):
    resp = httpx.get(
        f"{BASE_URLS['buyer']}/farmer/orders/",
        headers=auth_headers(farmer_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1


def test_farmer_order_lifecycle(farmer_token, buyer_token, produce_listing):
    """Place a fresh order then walk it through pending → confirmed → completed."""
    # Place a new order
    order_resp = httpx.post(
        f"{BASE_URLS['buyer']}/orders/",
        json={"produce_id": produce_listing["id"], "quantity_kg": 1.0},
        headers=auth_headers(buyer_token),
    )
    assert order_resp.status_code == 201
    order_id = order_resp.json()["id"]

    # Farmer confirms
    confirm = httpx.patch(
        f"{BASE_URLS['buyer']}/farmer/orders/{order_id}/status?new_status=confirmed",
        headers=auth_headers(farmer_token),
    )
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "confirmed"

    # Farmer completes
    complete = httpx.patch(
        f"{BASE_URLS['buyer']}/farmer/orders/{order_id}/status?new_status=completed",
        headers=auth_headers(farmer_token),
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"


def test_farmer_cannot_skip_to_completed(farmer_token, placed_order):
    """Cannot jump directly from pending to completed."""
    resp = httpx.patch(
        f"{BASE_URLS['buyer']}/farmer/orders/{placed_order['id']}/status?new_status=completed",
        headers=auth_headers(farmer_token),
    )
    assert resp.status_code == 400


def test_buyer_cannot_access_farmer_orders(buyer_token):
    resp = httpx.get(
        f"{BASE_URLS['buyer']}/farmer/orders/",
        headers=auth_headers(buyer_token),
    )
    assert resp.status_code == 403


# ── Internal API key on reduce-stock ──────────────────────────────────

def test_reduce_stock_rejects_missing_key(produce_listing):
    """Direct call without the internal key must be rejected."""
    resp = httpx.patch(
        f"{BASE_URLS['produce']}/produce/{produce_listing['id']}/reduce-stock",
        json={"quantity": 1.0},
    )
    assert resp.status_code == 403
