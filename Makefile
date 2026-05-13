# =============================================================================
# Soko — root Makefile
#
# Quick reference:
#   make setup   — first-time setup (network + .env files)
#   make start   — start the full stack (ML + core)
#   make stop    — stop the full stack
#   make restart — stop then start
#
#   make ml-up / make ml-down     — ML stack only
#   make core-up / make core-down — core stack only
# =============================================================================

# ── Compose handles ───────────────────────────────────────────────────────────
ML_DIR       := services/soko-ml
COMPOSE_ML   := docker compose -f $(ML_DIR)/docker-compose.yml --project-directory $(ML_DIR)
COMPOSE_DEV  := docker compose \
                  -f $(ML_DIR)/docker-compose.yml \
                  -f $(ML_DIR)/docker-compose.dev.yml \
                  --project-directory $(ML_DIR)
COMPOSE_CORE := docker compose -f docker-compose.yml

# ── Python venvs (ML layer) ───────────────────────────────────────────────────
PRICE_VENV   := $(ML_DIR)/price-prediction-service/.venv
REC_VENV     := $(ML_DIR)/recommendation-service/.venv
GATEWAY_VENV := $(ML_DIR)/ml-gateway-service/.venv
AGENT_VENV   := $(ML_DIR)/kafka-agent/.venv
DATA_VENV    := $(ML_DIR)/data-generator/.venv

# ── Core services that need .env files ───────────────────────────────────────
CORE_SERVICES := auth user produce order payment message notification blog ussd

.PHONY: setup start stop restart \
        bridge-network \
        ml-up ml-down ml-logs \
        core-up core-down core-logs core-restart \
        install generate-data train \
        dev dev-price dev-rec dev-gateway \
        infra-up infra-down kafka-topics kafka-ui redis-cli \
        logs logs-price logs-rec logs-gateway logs-agent \
        test test-price test-rec test-gateway \
        health smoke-test \
        clean clean-models clean-docker \
        help

# =============================================================================
# HELP
# =============================================================================

help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════╗"
	@echo "║                     Soko — Makefile Reference                       ║"
	@echo "╚══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "► RUNNING THE FULL STACK (recommended order for first time)"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  1. make setup       Create bridge network + all .env files"
	@echo "     ↳ Edit each services/*/.env with real secrets before continuing"
	@echo "  2. make start       Build and start ML stack then core stack"
	@echo "     ↳ API gateway    → http://localhost"
	@echo "     ↳ ML gateway     → http://localhost:8080"
	@echo ""
	@echo "  Subsequent runs:    make start   (skips rebuild if images unchanged)"
	@echo "  Tear everything down: make stop"
	@echo ""
	@echo "► FULL STACK"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make setup          First-time: bridge network + .env files for all services"
	@echo "  make start          Build and start the full stack (ML + core)"
	@echo "  make stop           Stop the full stack"
	@echo "  make restart        Stop then start the full stack"
	@echo ""
	@echo "► ML STACK"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make ml-up          Build and start the ML stack"
	@echo "     ↳ ML gateway     → http://localhost:8080"
	@echo "     ↳ Price service  → http://localhost:8094/docs"
	@echo "     ↳ Rec service    → http://localhost:8095/docs"
	@echo "  make ml-down        Stop and remove ML containers + volumes"
	@echo "  make ml-logs        Tail logs for all ML containers"
	@echo ""
	@echo "► CORE STACK"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make core-up        Build and start the core backend services"
	@echo "     ↳ All services   → http://localhost (via nginx)"
	@echo "  make core-down      Stop core containers"
	@echo "  make core-restart   Stop then start core containers"
	@echo "  make core-logs      Tail logs for all core containers"
	@echo ""
	@echo "► ML — LOCAL DEVELOPMENT"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make install        Create Python venvs and install ML dependencies"
	@echo "  make generate-data  Generate synthetic training data (farmers/buyers/prices)"
	@echo "  make train          Train price-prediction models locally"
	@echo "  make dev            Run ML stack with hot-reload (docker compose dev override)"
	@echo "  make dev-price      Run price service locally with uvicorn on :8094"
	@echo "  make dev-rec        Run recommendation service locally with uvicorn on :8095"
	@echo "  make dev-gateway    Run ML gateway locally with uvicorn on :8080"
	@echo ""
	@echo "► ML — INFRASTRUCTURE"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make infra-up       Start only Zookeeper, Kafka, and Redis"
	@echo "  make infra-down     Stop and remove infrastructure containers"
	@echo "  make kafka-topics   Create all required Kafka topics"
	@echo "  make kafka-ui       List all Kafka topics"
	@echo "  make redis-cli      Open a Redis CLI session inside the ML Redis container"
	@echo ""
	@echo "► LOGS"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make logs           Tail all ML stack logs"
	@echo "  make logs-price     Tail price-prediction-service logs"
	@echo "  make logs-rec       Tail recommendation-service logs"
	@echo "  make logs-gateway   Tail ml-gateway-service logs"
	@echo "  make logs-agent     Tail kafka-agent logs"
	@echo ""
	@echo "► TESTING"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make test           Run all ML service test suites"
	@echo "  make test-price     Run price-prediction-service tests only"
	@echo "  make test-rec       Run recommendation-service tests only"
	@echo "  make test-gateway   Run ml-gateway-service tests only"
	@echo ""
	@echo "► HEALTH & SMOKE"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make health         Hit /health on API gateway + all ML services"
	@echo "  make smoke-test     End-to-end: price prediction + recommendation calls"
	@echo ""
	@echo "► CLEAN"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make clean          Remove Python venvs and cached files"
	@echo "  make clean-models   Remove trained model .pkl files"
	@echo "  make clean-docker   Remove all containers, volumes, and images (both stacks)"
	@echo ""

# =============================================================================
# FIRST-TIME SETUP
# =============================================================================

setup: bridge-network
	@for svc in $(CORE_SERVICES); do \
	  if [ ! -f services/$$svc/.env ]; then \
	    cp services/$$svc/.env.example services/$$svc/.env; \
	    echo "  created  services/$$svc/.env"; \
	  else \
	    echo "  exists   services/$$svc/.env (skipped)"; \
	  fi; \
	done
	@if [ ! -f $(ML_DIR)/.env ]; then \
	  cp $(ML_DIR)/.env.example $(ML_DIR)/.env; \
	  echo "  created  $(ML_DIR)/.env"; \
	else \
	  echo "  exists   $(ML_DIR)/.env (skipped)"; \
	fi
	@echo ""
	@echo "Setup complete. Before running 'make start', open each .env and set:"
	@echo "  services/auth/.env         → SECRET_KEY, FRONTEND_URL"
	@echo "  services/*/.env            → INTERNAL_SECRET (same value in all services)"
	@echo "  services/payment/.env      → PESAPAL_CONSUMER_KEY / SECRET (optional)"
	@echo "  services/produce/.env      → CLOUDINARY_* (optional, for image uploads)"
	@echo "  services/notification/.env → AT_USERNAME / AT_API_KEY (optional, for SMS)"
	@echo "  services/ussd/.env         → AT_USERNAME / AT_API_KEY (optional)"

# =============================================================================
# SHARED NETWORK
# =============================================================================
# soko-ml-bridge connects the ML stack to nginx, order, and produce services.
# Created once; both docker-compose files reference it as external.

bridge-network:
	@docker network create soko-ml-bridge 2>/dev/null && \
	  echo "Bridge network soko-ml-bridge created." || \
	  echo "Bridge network soko-ml-bridge already exists."

# =============================================================================
# FULL STACK
# =============================================================================

start: bridge-network ml-up core-up
	@echo ""
	@echo "Full Soko stack is live:"
	@echo "  API gateway (all services) → http://localhost"
	@echo "  ML price predictions       → http://localhost/ml/price/predict"
	@echo "  ML recommendations         → http://localhost/ml/recommend/"
	@echo "  ML gateway (direct)        → http://localhost:8080"

stop: core-down ml-down

restart: stop start

# =============================================================================
# ML STACK
# =============================================================================

ml-up: bridge-network
	$(COMPOSE_ML) up --build -d
	@echo "ML stack live → http://localhost:8080  (gateway)"
	@echo "               http://localhost:8094  (price-prediction)"
	@echo "               http://localhost:8095  (recommendation)"

ml-down:
	$(COMPOSE_ML) down -v

ml-logs:
	$(COMPOSE_ML) logs -f

# Legacy aliases kept for backward compatibility
up: ml-up
down: ml-down

# =============================================================================
# CORE STACK
# =============================================================================

core-up:
	$(COMPOSE_CORE) up --build -d
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════════╗"
	@echo "║                     Soko Core Stack — Live                          ║"
	@echo "╚══════════════════════════════════════════════════════════════════════╝"
	@echo ""
	@docker compose ps
	@echo ""
	@echo "► SERVICES & DOCS"
	@echo "  ──────────────────────────────────────────────────────────────────"
	@echo "  API Gateway          →  http://localhost"
	@echo "  Auth Service         →  http://localhost/auth/docs"
	@echo "  User Service         →  http://localhost/users/docs"
	@echo "  Produce Service      →  http://localhost/listings/docs"
	@echo "  Order Service        →  http://localhost/orders/docs"
	@echo "  Payment Service      →  http://localhost/payments/docs"
	@echo "  Message Service      →  http://localhost/message/docs"
	@echo "  Notification Service →  http://localhost/notifications/docs"
	@echo "  Blog Service         →  http://localhost/posts/docs"
	@echo "  USSD Service         →  http://localhost/ussd/ (no docs)"
	@echo ""
	@echo "► DATABASES (internal — reachable only within soko_net)"
	@echo "  ──────────────────────────────────────────────────────────────────"
	@echo "  auth_db         →  postgresql://auth_user:auth_pass@auth_db:5432/auth_db"
	@echo "  user_db         →  postgresql://user_user:user_pass@user_db:5432/user_db"
	@echo "  produce_db      →  postgresql://produce_user:produce_pass@produce_db:5432/produce_db"
	@echo "  order_db        →  postgresql://order_user:order_pass@order_db:5432/order_db"
	@echo "  payment_db      →  postgresql://payment_user:payment_pass@payment_db:5432/payment_db"
	@echo "  message_db      →  postgresql://message_user:message_pass@message_db:5432/message_db"
	@echo "  notification_db →  postgresql://notification_user:notification_pass@notification_db:5432/notification_db"
	@echo "  blog_db         →  postgresql://blog_user:blog_pass@blog_db:5432/blog_db"
	@echo "  ussd_db         →  postgresql://ussd_user:ussd_pass@ussd_db:5432/ussd_db"
	@echo "  redis           →  redis://redis:6379"
	@echo ""
	@echo "► ML GATEWAY (if ml stack is running)"
	@echo "  ──────────────────────────────────────────────────────────────────"
	@echo "  Price predictions  →  http://localhost/ml/price/predict"
	@echo "  Recommendations    →  http://localhost/ml/recommend/"
	@echo ""

core-down:
	$(COMPOSE_CORE) down

core-restart: core-down core-up

core-logs:
	$(COMPOSE_CORE) logs -f

# =============================================================================
# ML — SETUP (local Python, training)
# =============================================================================

install:
	python3.12 -m venv $(PRICE_VENV)   && $(PRICE_VENV)/bin/pip install -q -r $(ML_DIR)/price-prediction-service/requirements.txt
	python3.12 -m venv $(REC_VENV)     && $(REC_VENV)/bin/pip install -q -r $(ML_DIR)/recommendation-service/requirements.txt
	python3.12 -m venv $(GATEWAY_VENV) && $(GATEWAY_VENV)/bin/pip install -q -r $(ML_DIR)/ml-gateway-service/requirements.txt
	python3.12 -m venv $(AGENT_VENV)   && $(AGENT_VENV)/bin/pip install -q -r $(ML_DIR)/kafka-agent/requirements.txt
	python3.12 -m venv $(DATA_VENV)    && $(DATA_VENV)/bin/pip install -q -r $(ML_DIR)/data-generator/requirements.txt
	@echo "All ML dependencies installed."
	@echo "Installing CmdStan 2.33.1 into Prophet's internal path (one-time, ~400 MB)..."
	$(PRICE_VENV)/bin/python -c "\
import prophet, pathlib, cmdstanpy; \
d = pathlib.Path(prophet.__file__).parent / 'stan_model'; \
target = d / 'cmdstan-2.33.1'; \
d.mkdir(parents=True, exist_ok=True); \
(print('CmdStan 2.33.1 already present, skipping.') if (target / 'Makefile').exists() \
else (print('Downloading + compiling CmdStan 2.33.1...'), \
cmdstanpy.install_cmdstan(dir=str(d), version='2.33.1'), \
print('CmdStan 2.33.1 installed.')))"

generate-data:
	@mkdir -p $(ML_DIR)/recommendation-service/data/raw
	OUTPUT_DIR=$(abspath $(ML_DIR)/recommendation-service/data/raw) \
	  $(DATA_VENV)/bin/python $(ML_DIR)/data-generator/generate_prices.py
	OUTPUT_DIR=$(abspath $(ML_DIR)/recommendation-service/data/raw) \
	  $(DATA_VENV)/bin/python $(ML_DIR)/data-generator/generate_profiles.py
	@echo "Data generated in $(ML_DIR)/recommendation-service/data/raw/"

train:
	@mkdir -p $(ML_DIR)/price-prediction-service/models
	cd $(ML_DIR)/price-prediction-service && \
	  MODEL_DIR=$(abspath $(ML_DIR)/price-prediction-service/models) \
	  DATA_DIR=$(abspath $(ML_DIR)/recommendation-service/data/raw) \
	  $(abspath $(PRICE_VENV))/bin/python -c \
	  "from src.predictor import train_all_models; train_all_models()"
	@echo "Models trained → $(ML_DIR)/price-prediction-service/models/"

# =============================================================================
# ML — DEVELOPMENT (local uvicorn with hot-reload)
# =============================================================================

dev:
	$(COMPOSE_DEV) up --build

dev-price:
	cd $(ML_DIR)/price-prediction-service && \
	  $(abspath $(PRICE_VENV))/bin/uvicorn src.main:app --host 0.0.0.0 --port 8094 --reload

dev-rec:
	cd $(ML_DIR)/recommendation-service && \
	  $(abspath $(REC_VENV))/bin/uvicorn src.main:app --host 0.0.0.0 --port 8095 --reload

dev-gateway:
	cd $(ML_DIR)/ml-gateway-service && \
	  $(abspath $(GATEWAY_VENV))/bin/uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

# =============================================================================
# ML — INFRASTRUCTURE HELPERS
# =============================================================================

infra-up:
	$(COMPOSE_ML) up -d zookeeper kafka kafka-init redis
	@echo "ML infrastructure starting (Kafka may take ~30s to be ready)."

infra-down:
	$(COMPOSE_ML) stop zookeeper kafka kafka-init redis
	$(COMPOSE_ML) rm -f zookeeper kafka kafka-init redis

kafka-topics:
	$(COMPOSE_ML) exec kafka kafka-topics --bootstrap-server localhost:9092 \
	  --create --if-not-exists --topic soko.transactions    --partitions 6 --replication-factor 1
	$(COMPOSE_ML) exec kafka kafka-topics --bootstrap-server localhost:9092 \
	  --create --if-not-exists --topic soko.interactions   --partitions 6 --replication-factor 1
	$(COMPOSE_ML) exec kafka kafka-topics --bootstrap-server localhost:9092 \
	  --create --if-not-exists --topic soko.price.requests --partitions 3 --replication-factor 1
	$(COMPOSE_ML) exec kafka kafka-topics --bootstrap-server localhost:9092 \
	  --create --if-not-exists --topic soko.price.results  --partitions 3 --replication-factor 1
	$(COMPOSE_ML) exec kafka kafka-topics --bootstrap-server localhost:9092 \
	  --create --if-not-exists --topic soko.ml.events      --partitions 2 --replication-factor 1
	$(COMPOSE_ML) exec kafka kafka-topics --bootstrap-server localhost:9092 \
	  --create --if-not-exists --topic soko.dlq            --partitions 2 --replication-factor 1
	@echo "All Kafka topics created."

kafka-ui:
	$(COMPOSE_ML) exec kafka kafka-topics --bootstrap-server localhost:9092 --list

redis-cli:
	$(COMPOSE_ML) exec redis redis-cli

# =============================================================================
# ML — LOGGING
# =============================================================================

logs:
	$(COMPOSE_ML) logs -f

logs-price:
	$(COMPOSE_ML) logs -f price-prediction-service

logs-rec:
	$(COMPOSE_ML) logs -f recommendation-service

logs-gateway:
	$(COMPOSE_ML) logs -f ml-gateway-service

logs-agent:
	$(COMPOSE_ML) logs -f kafka-agent

# =============================================================================
# TESTING
# =============================================================================

test: test-price test-rec test-gateway

test-price:
	$(PRICE_VENV)/bin/pytest $(ML_DIR)/price-prediction-service/tests/ -v

test-rec:
	$(REC_VENV)/bin/pytest $(ML_DIR)/recommendation-service/tests/ -v

test-gateway:
	$(GATEWAY_VENV)/bin/pytest $(ML_DIR)/ml-gateway-service/tests/ -v

# =============================================================================
# HEALTH & SMOKE
# =============================================================================

health:
	@echo "=== API Gateway ===" && \
	  curl -sf http://localhost/health || echo "UNREACHABLE"
	@echo "=== ML Gateway ===" && \
	  curl -sf http://localhost:8080/health | python3 -m json.tool || echo "UNREACHABLE"
	@echo "=== Price Service ===" && \
	  curl -sf http://localhost:8094/health | python3 -m json.tool || echo "UNREACHABLE"
	@echo "=== Recommendation Service ===" && \
	  curl -sf http://localhost:8095/health | python3 -m json.tool || echo "UNREACHABLE"

smoke-test:
	@echo "=== Smoke: Price Prediction ==="
	@curl -sf -X POST http://localhost:8080/price/predict \
	  -H 'Content-Type: application/json' \
	  -d '{"market":"Kisenyi_Kampala","crop":"maize_grain","weeks_ahead":4}' \
	  | python3 -m json.tool
	@echo "=== Smoke: Farmers for Buyer ==="
	@curl -sf "http://localhost:8080/recommend/farmers-for-buyer/B0001?top_n=3" | python3 -m json.tool
	@echo "=== Smoke: Buyers for Farmer ==="
	@curl -sf "http://localhost:8080/recommend/buyers-for-farmer/F0001?top_n=3" | python3 -m json.tool

# =============================================================================
# CLEAN
# =============================================================================

clean:
	find $(ML_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(ML_DIR) -name "*.pyc" -delete 2>/dev/null || true
	rm -rf $(PRICE_VENV) $(REC_VENV) $(GATEWAY_VENV) $(AGENT_VENV) $(DATA_VENV)
	rm -f $(ML_DIR)/recommendation-service/data/raw/*.csv
	@echo "Cleaned."

clean-models:
	rm -f $(ML_DIR)/price-prediction-service/models/*.pkl
	@echo "Model files removed."

clean-docker:
	$(COMPOSE_ML) down -v --rmi all
	$(COMPOSE_CORE) down --rmi all
	@echo "All containers, volumes, and images removed."
