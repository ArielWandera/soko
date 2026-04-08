"""
Soko load test — models three realistic user types:

  BrowseUser   (weight 5) — anonymous, hits public read endpoints
  BuyerUser    (weight 3) — logs in, browses, gets recommendations, places orders
  FarmerUser   (weight 2) — logs in, manages listings and checks incoming orders

How users are managed:
  Before the test starts, a pool of buyer and farmer accounts is created
  sequentially (one at a time). During the test each virtual user just picks
  a credential from the pool and logs in — no bcrypt stampede on startup.
  Any number of virtual users can share the pool.

Run (web UI):
  locust -f tests/load/locustfile.py --host http://localhost

Run headless (50 users, 5/s spawn, 2 minutes):
  locust -f tests/load/locustfile.py --host http://localhost \
         --headless -u 50 -r 5 --run-time 2m
"""

import random
import threading
import time
import requests as _requests
from locust import HttpUser, task, between, events


# ---------------------------------------------------------------------------
# Service addresses (direct, bypasses nginx)
# ---------------------------------------------------------------------------

AUTH_HOST    = "http://localhost:8001"
FARMER_HOST  = "http://localhost:8002"
BUYER_HOST   = "http://localhost:8003"
PRODUCE_HOST = "http://localhost:8004"
RECO_HOST    = "http://localhost:8005"

DISTRICTS  = ["Kampala", "Wakiso", "Mukono", "Jinja", "Mbale", "Gulu", "Mbarara"]
CATEGORIES = ["vegetables", "grains", "fruits", "dairy", "herbs"]

# Pool sizes — only affects how many DB accounts exist, not how many
# virtual users you can run. 500 virtual users can share 15 buyer accounts.
POOL_BUYERS  = 15
POOL_FARMERS = 10

# Shared state — populated once before the test, read-only during it
_buyer_creds:  list[dict] = []   # [{"email": ..., "password": ...}]
_farmer_creds: list[dict] = []   # [{"email": ..., "password": ..., "listing_id": ...}]
_produce_ids:  list       = []
_setup_lock = threading.Lock()
_setup_done = False


# ---------------------------------------------------------------------------
# Pre-test setup
# ---------------------------------------------------------------------------

def _login(email: str, password: str) -> str | None:
    resp = _requests.post(
        f"{AUTH_HOST}/auth/login",
        data={"username": email, "password": password},
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json().get("access_token")
    return None


def _setup_buyer(i: int):
    email    = f"load_buyer_{i:03d}@sokoload.io"
    password = "Loadtest123!"
    phone    = f"+25670{i:07d}"

    # Register — safe to retry, 409 means already exists
    _requests.post(f"{AUTH_HOST}/auth/register", json={
        "email": email,
        "full_name": f"Load Buyer {i:03d}",
        "password": password,
        "role": "buyer",
    }, timeout=15)

    token = _login(email, password)
    if not token:
        return

    # Create profile — 400 means already exists, both are fine
    _requests.post(f"{BUYER_HOST}/buyers/profile", json={
        "full_name": f"Load Buyer {i:03d}",
        "phone": phone,
        "district": random.choice(DISTRICTS),
    }, headers={"Authorization": f"Bearer {token}"}, timeout=10)

    _buyer_creds.append({"email": email, "password": password})


def _setup_farmer(i: int):
    email    = f"load_farmer_{i:03d}@sokoload.io"
    password = "Loadtest123!"
    phone    = f"+25671{i:07d}"

    _requests.post(f"{AUTH_HOST}/auth/register", json={
        "email": email,
        "full_name": f"Load Farmer {i:03d}",
        "password": password,
        "role": "farmer",
    }, timeout=15)

    token = _login(email, password)
    if not token:
        return

    _requests.post(f"{FARMER_HOST}/farmers/profile", json={
        "full_name": f"Load Farmer {i:03d}",
        "phone": phone,
        "district": random.choice(DISTRICTS),
    }, headers={"Authorization": f"Bearer {token}"}, timeout=10)

    # Create a produce listing so farmers have something to manage
    resp = _requests.post(f"{PRODUCE_HOST}/produce/", json={
        "name": f"Load Produce {i:03d}",
        "description": "Load test item",
        "category": random.choice(CATEGORIES),
        "unit": "kg",
        "quantity": 1000.0,
        "price_per_unit": random.randint(500, 8000),
        "district": random.choice(DISTRICTS),
    }, headers={"Authorization": f"Bearer {token}"}, timeout=10)

    listing_id = resp.json().get("id") if resp.status_code == 201 else None
    if listing_id:
        _produce_ids.append(listing_id)

    _farmer_creds.append({
        "email": email,
        "password": password,
        "listing_id": listing_id,
    })


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Runs once when a test starts. Creates pool accounts sequentially so
    bcrypt never runs concurrently — then the actual test has no auth overhead.
    """
    global _setup_done
    with _setup_lock:
        if _setup_done:
            return

        print(f"\n[setup] Creating {POOL_BUYERS} buyers and {POOL_FARMERS} farmers "
              f"(sequential, one bcrypt at a time)...")

        for i in range(POOL_BUYERS):
            _setup_buyer(i)
            print(f"  buyer  {i+1:02d}/{POOL_BUYERS} ready")

        for i in range(POOL_FARMERS):
            _setup_farmer(i)
            print(f"  farmer {i+1:02d}/{POOL_FARMERS} ready")

        # Seed additional produce ids from the public listing
        resp = _requests.get(f"{PRODUCE_HOST}/produce/", params={"limit": 50}, timeout=10)
        if resp.status_code == 200:
            for item in resp.json().get("items", []):
                pid = item.get("id")
                if pid and pid not in _produce_ids:
                    _produce_ids.append(pid)

        print(f"[setup] Done — {len(_buyer_creds)} buyers, {len(_farmer_creds)} farmers, "
              f"{len(_produce_ids)} produce listings in pool.\n")
        _setup_done = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Anonymous browser — public read traffic (weight 5 = 50% of users)
# ---------------------------------------------------------------------------

class BrowseUser(HttpUser):
    weight = 5
    wait_time = between(1, 4)

    def on_start(self):
        self._local_produce_ids = list(_produce_ids)

    @task(5)
    def browse_produce_listings(self):
        params = {"page": random.randint(1, 3), "limit": 20}
        cat = random.choice([None] + CATEGORIES)
        if cat:
            params["category"] = cat
        self.client.get(f"{PRODUCE_HOST}/produce/", params=params, name="/produce/")

    @task(3)
    def view_price_predictions(self):
        cat = random.choice([None] + CATEGORIES)
        params = {"category": cat} if cat else {}
        self.client.get(
            f"{PRODUCE_HOST}/produce/prices/predictions",
            params=params,
            name="/produce/prices/predictions",
        )

    @task(2)
    def browse_farmers(self):
        self.client.get(
            f"{FARMER_HOST}/farmers/",
            params={"page": 1, "limit": 20},
            name="/farmers/",
        )

    @task(2)
    def view_single_produce(self):
        if not self._local_produce_ids:
            return
        pid = random.choice(self._local_produce_ids)
        self.client.get(f"{PRODUCE_HOST}/produce/{pid}", name="/produce/:id")

    @task(1)
    def auth_health(self):
        self.client.get(f"{AUTH_HOST}/health", name="/auth/health")


# ---------------------------------------------------------------------------
# Buyer — authenticated (weight 3 = 30% of users)
# ---------------------------------------------------------------------------

class BuyerUser(HttpUser):
    weight = 3
    wait_time = between(2, 6)

    def on_start(self):
        self._token = None
        self._produce_ids = list(_produce_ids)

        # Wait for setup to finish before trying to log in
        deadline = time.time() + 300
        while not _setup_done and time.time() < deadline:
            time.sleep(2)

        if not _buyer_creds:
            return

        cred = random.choice(_buyer_creds)
        resp = self.client.post(
            f"{AUTH_HOST}/auth/login",
            data={"username": cred["email"], "password": cred["password"]},
            name="/auth/login",
        )
        if resp.status_code == 200:
            self._token = resp.json().get("access_token")

    @task(4)
    def browse_produce(self):
        if not self._token:
            return
        resp = self.client.get(
            f"{BUYER_HOST}/produce/",
            params={"page": 1, "limit": 20},
            headers=_auth_headers(self._token),
            name="/produce/ (buyer)",
        )
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            ids = [i["id"] for i in items if "id" in i]
            if ids:
                self._produce_ids = ids

    @task(3)
    def get_recommendations(self):
        if not self._token:
            return
        self.client.get(
            f"{RECO_HOST}/recommendations/",
            headers=_auth_headers(self._token),
            name="/recommendations/",
        )

    @task(2)
    def view_single_produce(self):
        if not self._token or not self._produce_ids:
            return
        pid = random.choice(self._produce_ids)
        self.client.get(
            f"{BUYER_HOST}/produce/{pid}",
            headers=_auth_headers(self._token),
            name="/produce/:id (buyer)",
        )

    @task(2)
    def list_orders(self):
        if not self._token:
            return
        self.client.get(
            f"{BUYER_HOST}/orders/",
            headers=_auth_headers(self._token),
            name="/orders/ (list)",
        )

    @task(1)
    def place_order(self):
        if not self._token or not self._produce_ids:
            return
        pid = random.choice(self._produce_ids)
        self.client.post(
            f"{BUYER_HOST}/orders/",
            json={"produce_id": pid, "quantity_kg": round(random.uniform(1, 10), 1)},
            headers=_auth_headers(self._token),
            name="/orders/ (place)",
        )


# ---------------------------------------------------------------------------
# Farmer — authenticated (weight 2 = 20% of users)
# ---------------------------------------------------------------------------

class FarmerUser(HttpUser):
    weight = 2
    wait_time = between(3, 8)

    def on_start(self):
        self._token = None
        self._listing_id = None

        # Wait for setup to finish before trying to log in
        deadline = time.time() + 300
        while not _setup_done and time.time() < deadline:
            time.sleep(2)

        if not _farmer_creds:
            return

        cred = random.choice(_farmer_creds)
        resp = self.client.post(
            f"{AUTH_HOST}/auth/login",
            data={"username": cred["email"], "password": cred["password"]},
            name="/auth/login",
        )
        if resp.status_code == 200:
            self._token = resp.json().get("access_token")
            self._listing_id = cred.get("listing_id")

    @task(4)
    def check_incoming_orders(self):
        if not self._token:
            return
        self.client.get(
            f"{BUYER_HOST}/farmer/orders/",
            headers=_auth_headers(self._token),
            name="/farmer/orders/",
        )

    @task(3)
    def view_my_listings(self):
        if not self._token:
            return
        self.client.get(
            f"{PRODUCE_HOST}/produce/farmer/mine",
            headers=_auth_headers(self._token),
            name="/produce/farmer/mine",
        )

    @task(2)
    def update_listing_price(self):
        if not self._token or not self._listing_id:
            return
        self.client.patch(
            f"{PRODUCE_HOST}/produce/{self._listing_id}",
            json={"price_per_unit": random.randint(500, 8000)},
            headers=_auth_headers(self._token),
            name="/produce/:id (update)",
        )

    @task(1)
    def view_profile(self):
        if not self._token:
            return
        self.client.get(
            f"{FARMER_HOST}/farmers/profile",
            headers=_auth_headers(self._token),
            name="/farmers/profile",
        )
