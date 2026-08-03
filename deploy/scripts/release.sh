#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY_DIR="$ROOT_DIR/deploy"
ENV_FILE="$DEPLOY_DIR/.env.production"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.prod.yml"
RUNTIME_NGINX="$DEPLOY_DIR/nginx/runtime/default.conf"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Xato: $ENV_FILE topilmadi. Avval .env.production.example dan nusxa yarating."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Xato: Docker o‘rnatilmagan."
  exit 1
fi

mkdir -p "$DEPLOY_DIR/nginx/runtime" "$DEPLOY_DIR/certbot/www" "$DEPLOY_DIR/certbot/conf"
if [[ ! -f "$RUNTIME_NGINX" ]]; then
  cp "$DEPLOY_DIR/nginx/http.conf" "$RUNTIME_NGINX"
fi

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

"${COMPOSE[@]}" config --quiet
"${COMPOSE[@]}" build --pull backend frontend
"${COMPOSE[@]}" up -d db backend frontend nginx

echo "Containerlar ishga tushdi. Holat:"
"${COMPOSE[@]}" ps
echo "Loglarni ko‘rish: docker compose --env-file deploy/.env.production -f deploy/docker-compose.prod.yml logs -f"
