#!/bin/bash
# Writes all service .env files from environment variables.
# Called by the GitHub Actions deploy workflow on the EC2 host.
# All variables must already be exported in the shell environment.
set -euo pipefail

write_env() {
  local path="$1"; shift
  printf '%s\n' "$@" > "$path"
  echo "  wrote $path"
}

# Derive the public IP for service URLs when no domain is set yet.
SERVER_IP=$(curl -sf http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
FRONTEND_URL="${FRONTEND_URL:-http://${SERVER_IP}}"

echo "Writing .env files (FRONTEND_URL=${FRONTEND_URL})..."

write_env services/auth/.env \
  "DATABASE_URL=postgresql://auth_user:auth_pass@auth_db:5432/auth_db" \
  "SECRET_KEY=${AUTH_SECRET_KEY}" \
  "GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}" \
  "GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-}" \
  "GOOGLE_REDIRECT_URI=${FRONTEND_URL}/auth/google/callback" \
  "FRONTEND_URL=${FRONTEND_URL}" \
  "USER_SERVICE_URL=http://user_service:8002"

write_env services/user/.env \
  "DATABASE_URL=postgresql://user_user:user_pass@user_db:5432/user_db" \
  "INTERNAL_SECRET=${INTERNAL_SECRET}" \
  "AUTH_SERVICE_URL=http://auth_service:8001"

write_env services/produce/.env \
  "DATABASE_URL=postgresql://produce_user:produce_pass@produce_db:5432/produce_db" \
  "INTERNAL_SECRET=${INTERNAL_SECRET}" \
  "USER_SERVICE_URL=http://user_service:8002" \
  "ML_GATEWAY_URL=http://ml-gateway:8000" \
  "CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME:-}" \
  "CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY:-}" \
  "CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET:-}" \
  "REDIS_URL=redis://redis:6379/0"

write_env services/order/.env \
  "DATABASE_URL=postgresql://order_user:order_pass@order_db:5432/order_db" \
  "INTERNAL_SECRET=${INTERNAL_SECRET}" \
  "PRODUCE_SERVICE_URL=http://produce_service:8003" \
  "USER_SERVICE_URL=http://user_service:8002" \
  "PAYMENT_SERVICE_URL=http://payment_service:8005" \
  "NOTIFICATION_SERVICE_URL=http://notification_service:8007" \
  "KAFKA_BOOTSTRAP_SERVERS=kafka:9092" \
  "KAFKA_TRANSACTION_TOPIC=soko.transactions"

write_env services/payment/.env \
  "DATABASE_URL=postgresql://payment_user:payment_pass@payment_db:5432/payment_db" \
  "INTERNAL_SECRET=${INTERNAL_SECRET}" \
  "ORDER_SERVICE_URL=http://order_service:8004" \
  "USER_SERVICE_URL=http://user_service:8002" \
  "NOTIFICATION_SERVICE_URL=http://notification_service:8007" \
  "FRONTEND_URL=${FRONTEND_URL}" \
  "PESAPAL_CONSUMER_KEY=${PESAPAL_CONSUMER_KEY:-}" \
  "PESAPAL_CONSUMER_SECRET=${PESAPAL_CONSUMER_SECRET:-}" \
  "PESAPAL_ENV=${PESAPAL_ENV:-sandbox}" \
  "PESAPAL_IPN_URL=${FRONTEND_URL}/payments/webhook/pesapal/ipn" \
  "PESAPAL_CALLBACK_URL=${FRONTEND_URL}/payments/webhook/pesapal/callback"

write_env services/message/.env \
  "DATABASE_URL=postgresql://message_user:message_pass@message_db:5432/message_db" \
  "INTERNAL_SECRET=${INTERNAL_SECRET}" \
  "SECRET_KEY=${AUTH_SECRET_KEY}" \
  "USER_SERVICE_URL=http://user_service:8002" \
  "PRODUCE_SERVICE_URL=http://produce_service:8003" \
  "NOTIFICATION_SERVICE_URL=http://notification_service:8007"

write_env services/notification/.env \
  "DATABASE_URL=postgresql://notification_user:notification_pass@notification_db:5432/notification_db" \
  "INTERNAL_SECRET=${INTERNAL_SECRET}" \
  "SECRET_KEY=${AUTH_SECRET_KEY}" \
  "ALGORITHM=HS256" \
  "USER_SERVICE_URL=http://user_service:8002" \
  "AT_USERNAME=${AT_USERNAME:-sandbox}" \
  "AT_API_KEY=${AT_API_KEY:-}" \
  "AT_SENDER_ID=${AT_SENDER_ID:-}"

write_env services/blog/.env \
  "DATABASE_URL=postgresql://blog_user:blog_pass@blog_db:5432/blog_db" \
  "INTERNAL_SECRET=${INTERNAL_SECRET}" \
  "REDIS_URL=redis://redis:6379/1" \
  "USER_SERVICE_URL=http://user_service:8002" \
  "CLOUDINARY_CLOUD_NAME=${CLOUDINARY_CLOUD_NAME:-}" \
  "CLOUDINARY_API_KEY=${CLOUDINARY_API_KEY:-}" \
  "CLOUDINARY_API_SECRET=${CLOUDINARY_API_SECRET:-}"

write_env services/ussd/.env \
  "DATABASE_URL=postgresql://ussd_user:ussd_pass@ussd_db:5432/ussd_db" \
  "INTERNAL_SECRET=${INTERNAL_SECRET}" \
  "AT_USERNAME=${AT_USERNAME:-sandbox}" \
  "AT_API_KEY=${AT_API_KEY:-}" \
  "PRODUCE_SERVICE_URL=http://produce_service:8003" \
  "ORDER_SERVICE_URL=http://order_service:8004" \
  "AUTH_SERVICE_URL=http://auth_service:8001" \
  "USER_SERVICE_URL=http://user_service:8002" \
  "NOTIFICATION_SERVICE_URL=http://notification_service:8007"

# ML — no secrets, all config values from the example
cp services/soko-ml/.env.example services/soko-ml/.env

echo "Done."
