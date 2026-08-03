#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "Foydalanish: $0 DOMAIN EMAIL [QO‘SHIMCHA_DOMAIN]"
  echo "Misol: $0 bilimyol.uz admin@bilimyol.uz www.bilimyol.uz"
  exit 1
fi

PRIMARY_DOMAIN="$1"
EMAIL="$2"
ALT_DOMAIN="${3:-}"

if [[ ! "$PRIMARY_DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "Xato: domain formati noto‘g‘ri."
  exit 1
fi
if [[ -n "$ALT_DOMAIN" && ! "$ALT_DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "Xato: qo‘shimcha domain formati noto‘g‘ri."
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DEPLOY_DIR="$ROOT_DIR/deploy"
ENV_FILE="$DEPLOY_DIR/.env.production"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.prod.yml"
TEMPLATE="$DEPLOY_DIR/nginx/https.template.conf"
TARGET="$DEPLOY_DIR/nginx/runtime/default.conf"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Xato: $ENV_FILE topilmadi."
  exit 1
fi

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
CERTBOT_DOMAINS=(-d "$PRIMARY_DOMAIN")
SERVER_NAMES="$PRIMARY_DOMAIN"
if [[ -n "$ALT_DOMAIN" ]]; then
  CERTBOT_DOMAINS+=(-d "$ALT_DOMAIN")
  SERVER_NAMES="$SERVER_NAMES $ALT_DOMAIN"
fi

"${COMPOSE[@]}" run --rm certbot certonly \
  --webroot --webroot-path /var/www/certbot \
  --email "$EMAIL" --agree-tos --no-eff-email \
  "${CERTBOT_DOMAINS[@]}"

TEMP_CONFIG="$(mktemp "$DEPLOY_DIR/nginx/runtime/default.conf.XXXXXX")"
sed \
  -e "s/__DOMAIN__/$SERVER_NAMES/g" \
  -e "s/__CERT_DOMAIN__/$PRIMARY_DOMAIN/g" \
  "$TEMPLATE" > "$TEMP_CONFIG"
mv "$TEMP_CONFIG" "$TARGET"

"${COMPOSE[@]}" exec nginx nginx -t
"${COMPOSE[@]}" restart nginx

echo "SSL yoqildi: https://$PRIMARY_DOMAIN"
