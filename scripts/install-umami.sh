#!/usr/bin/env bash
set -euo pipefail

deploy_host="${DEPLOY_HOST:-150.158.127.73}"
deploy_user="${DEPLOY_USER:-ubuntu}"
deploy_key="${DEPLOY_KEY:-/Users/zhaoqr/.ssh/id_rsa}"
fitness_root="${FITNESS_ROOT:-/home/zhaoqr/fitness}"
remote_target="${deploy_user}@${deploy_host}"

ssh -i "$deploy_key" -o IdentitiesOnly=yes -o BatchMode=yes "$remote_target" "FITNESS_ROOT='$fitness_root' bash -s" <<'REMOTE'
set -euo pipefail

caddyfile="$FITNESS_ROOT/Caddyfile"
umami_dir="$FITNESS_ROOT/umami"
backup_dir="$FITNESS_ROOT/.umami-backups/$(date -u +%Y%m%dT%H%M%SZ)"
caddy_container="$(sudo docker ps --filter label=com.docker.compose.service=caddy --format '{{.ID}}' | head -n 1)"

[ -n "$caddy_container" ]
[ -f "$caddyfile" ]
caddy_network="$(sudo docker inspect -f '{{range $name, $network := .NetworkSettings.Networks}}{{$name}}{{end}}' "$caddy_container")"
[ -n "$caddy_network" ]

sudo install -d -m 700 "$umami_dir" "$backup_dir"
sudo cp "$caddyfile" "$backup_dir/Caddyfile"

if [ ! -f "$umami_dir/.env" ]; then
  app_secret="$(openssl rand -hex 32)"
  db_password="$(openssl rand -hex 24)"
  printf 'UMAMI_APP_SECRET=%s\nUMAMI_DB_PASSWORD=%s\n' "$app_secret" "$db_password" | sudo tee "$umami_dir/.env" >/dev/null
  sudo chmod 600 "$umami_dir/.env"
fi

cat <<COMPOSE | sudo tee "$umami_dir/docker-compose.yml" >/dev/null
services:
  umami:
    image: docker.umami.is/umami-software/umami:postgresql-latest
    container_name: fitstudy-umami
    restart: unless-stopped
    init: true
    env_file: .env
    environment:
      DATABASE_URL: postgresql://umami:\${UMAMI_DB_PASSWORD}@db:5432/umami
      APP_SECRET: \${UMAMI_APP_SECRET}
    depends_on:
      db:
        condition: service_healthy
    networks:
      default:
      caddy:
        aliases:
          - fitstudy-umami

  db:
    image: postgres:16-alpine
    container_name: fitstudy-umami-db
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_DB: umami
      POSTGRES_USER: umami
      POSTGRES_PASSWORD: \${UMAMI_DB_PASSWORD}
    volumes:
      - umami_db:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U umami -d umami"]
      interval: 10s
      timeout: 5s
      retries: 10

volumes:
  umami_db:

networks:
  caddy:
    external: true
    name: $caddy_network
COMPOSE

if ! sudo grep -q '^analytics\.fitstudy\.cn' "$caddyfile"; then
  printf '\nanalytics.fitstudy.cn {\n  reverse_proxy fitstudy-umami:3000\n}\n' | sudo tee -a "$caddyfile" >/dev/null
fi

if ! sudo docker exec "$caddy_container" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile; then
  sudo cp "$backup_dir/Caddyfile" "$caddyfile"
  exit 1
fi

if ! sudo docker compose -f "$umami_dir/docker-compose.yml" --env-file "$umami_dir/.env" up -d; then
  sudo cp "$backup_dir/Caddyfile" "$caddyfile"
  exit 1
fi

sudo docker exec "$caddy_container" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
printf 'Umami deployed: https://analytics.fitstudy.cn\n'
REMOTE
