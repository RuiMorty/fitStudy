#!/usr/bin/env bash
set -euo pipefail

deploy_host="${DEPLOY_HOST:-150.158.127.73}"
deploy_user="${DEPLOY_USER:-ubuntu}"
fitness_root="${FITNESS_ROOT:-/home/zhaoqr/fitness}"
remote_target="${deploy_user}@${deploy_host}"

ssh "$remote_target" "FITNESS_ROOT='$fitness_root' bash -s" <<'REMOTE'
set -euo pipefail

caddyfile="$FITNESS_ROOT/Caddyfile"
backup="$FITNESS_ROOT/Caddyfile.backup-$(date -u +%Y%m%dT%H%M%SZ)"
caddy_container="$(sudo docker ps --filter label=com.docker.compose.service=caddy --format '{{.ID}}' | head -n 1)"

[ -f "$caddyfile" ]
[ -n "$caddy_container" ]
sudo cp "$caddyfile" "$backup"

sudo tee "$caddyfile" >/dev/null <<'CADDY'
fitstudy.cn, www.fitstudy.cn {
  root * /srv
  encode gzip zstd

  @root path /
  redir @root /home/ temporary

  @versioned_assets path /html/assets/*
  header @versioned_assets Cache-Control "public, max-age=31536000, immutable"

  @code_assets path *.css *.js
  header @code_assets Cache-Control "public, max-age=86400"

  @course_data path /fitness_syllabus.md /reviews.json /progress.json
  header @course_data Cache-Control "public, max-age=300"

  file_server
}

analytics.fitstudy.cn {
  reverse_proxy fitstudy-umami:3000
}
CADDY

if ! sudo docker exec "$caddy_container" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile; then
  sudo cp "$backup" "$caddyfile"
  exit 1
fi

sudo docker exec "$caddy_container" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
printf 'Caddy delivery optimization applied. Backup: %s\n' "$backup"
REMOTE
