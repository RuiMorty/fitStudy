#!/usr/bin/env bash
set -euo pipefail

deploy_host="${DEPLOY_HOST:-150.158.127.73}"
deploy_user="${DEPLOY_USER:-ubuntu}"
deploy_path="${DEPLOY_PATH:-/home/zhaoqr/fitness/site}"
deploy_sudo="${DEPLOY_SUDO:-0}"
backup_id="${1:-}"
remote_target="${deploy_user}@${deploy_host}"

remote_command="SITE_DIR='$deploy_path' BACKUP_ID='$backup_id' bash -s"
ssh_options=()
if [ "$deploy_sudo" = "1" ]; then
  remote_command="sudo env SITE_DIR='$deploy_path' BACKUP_ID='$backup_id' bash -s"
  ssh_options=(-tt)
fi

ssh "${ssh_options[@]}" "$remote_target" "$remote_command" <<'REMOTE'
set -euo pipefail

backup_root="$SITE_DIR/.deploy-backups"
targets=(index.html app.js styles.css fitness_syllabus.md reviews.json progress.json html)

if [ -n "$BACKUP_ID" ]; then
  backup_dir="$backup_root/$BACKUP_ID"
else
  backup_dir="$(find "$backup_root" -mindepth 1 -maxdepth 1 -type d ! -name 'failed-*' -print | sort | tail -n 1)"
fi

[ -n "$backup_dir" ]
[ -d "$backup_dir" ]

rollback_dir="$backup_root/rollback-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$rollback_dir"
for target in "${targets[@]}"; do
  if [ -e "$SITE_DIR/$target" ]; then
    mv "$SITE_DIR/$target" "$rollback_dir/$target"
  fi
  if [ -e "$backup_dir/$target" ]; then
    mv "$backup_dir/$target" "$SITE_DIR/$target"
  fi
done

printf 'Rolled back from %s. Replaced files: %s\n' "$backup_dir" "$rollback_dir"
REMOTE
