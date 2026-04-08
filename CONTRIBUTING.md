# Contributing to Soko

## Before you start

- All changes must go through a pull request — direct pushes to `main` are blocked.
- Your PR must pass both CI checks (`lint` and `integration-tests`) and receive at least one approval before it can be merged.

## Services overview

| Service | Port | Responsibility |
|---|---|---|
| auth | 8001 | Registration, login, JWT |
| farmer | 8002 | Farmer profiles |
| buyer | 8003 | Buyer profiles, orders, reviews |
| produce | 8004 | Produce listings |
| recommendation | 8005 | Personalised recommendations |

Each service lives in `services/<name>/` and has its own database. Services communicate via RabbitMQ events and authenticate requests using the shared JWT secret.

## Running locally

**Requirements:** Docker Desktop (with Compose v2), Python 3.11+

```bash
# Start everything
docker compose up --build -d

# Verify all services are up
curl http://localhost:8001/health
curl http://localhost:8004/health
```

To rebuild a single service after editing its code:

```bash
docker compose up --build -d <service_name>
# e.g. docker compose up --build -d auth_service
```

## Running the tests

```bash
pip install -r tests/integration/requirements.txt
python -m pytest tests/integration/ -v --tb=short
```

Tests expect all services to be running locally on their default ports. The full suite takes around 2–3 minutes because some tests poll for async RabbitMQ events.

## Linting

We use [ruff](https://docs.astral.sh/ruff/). Run it before pushing:

```bash
pip install ruff
ruff check services/auth/app services/farmer/app services/buyer/app services/produce/app services/recommendation/app
```

CI will fail on any lint error.

## Pull request checklist

- [ ] `ruff check` passes with no errors
- [ ] All integration tests pass locally (`pytest tests/integration/`)
- [ ] New endpoints have a corresponding integration test
- [ ] Changes to the auth service (JWT shape, user fields) are coordinated with all other services — they all decode the same token

## User ID convention

All inter-service user identifiers are UUIDs (strings), sourced from the auth service. Never store or accept bare integer user IDs across service boundaries.

## Event contracts

RabbitMQ event schemas are documented in [CONTRACTS.md](CONTRACTS.md). If you change a published event's shape, update that file and notify the team — consumers in other services will break silently otherwise.
