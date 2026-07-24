#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
deploy_host="${DEPLOY_HOST:-150.158.127.73}"
deploy_user="${DEPLOY_USER:-ubuntu}"
deploy_path="${DEPLOY_PATH:-/home/zhaoqr/fitness/site}"
deploy_sudo="${DEPLOY_SUDO:-0}"
release_id="$(date -u +%Y%m%dT%H%M%SZ)"
remote_archive="/tmp/fitstudy-site-${release_id}.tar.gz"
remote_target="${deploy_user}@${deploy_host}"

"$project_dir/scripts/package-site.sh"
scp "$project_dir/fitstudy-site.tar.gz" "${remote_target}:${remote_archive}"

remote_command="SITE_DIR='$deploy_path' ARCHIVE='$remote_archive' RELEASE_ID='$release_id' bash -s"
ssh_options=()
if [ "$deploy_sudo" = "1" ]; then
  remote_command="sudo env SITE_DIR='$deploy_path' ARCHIVE='$remote_archive' RELEASE_ID='$release_id' bash -s"
  ssh_options=(-tt)
fi

ssh ${ssh_options+"${ssh_options[@]}"} "$remote_target" "$remote_command" <<'REMOTE'
set -euo pipefail

backup_root="$SITE_DIR/.deploy-backups"
backup_dir="$backup_root/$RELEASE_ID"
failed_dir="$backup_root/failed-$RELEASE_ID"
targets=(index.html app.js styles.css fitness_syllabus.md reviews.json progress.json html home library)

[ -d "$SITE_DIR" ]
mkdir -p "$backup_dir"
tar -tzf "$ARCHIVE" >/dev/null

for target in "${targets[@]}"; do
  if [ -e "$SITE_DIR/$target" ]; then
    mv "$SITE_DIR/$target" "$backup_dir/$target"
  fi
done

if ! tar -xzf "$ARCHIVE" -C "$SITE_DIR"; then
  mkdir -p "$failed_dir"
  for target in "${targets[@]}"; do
    if [ -e "$SITE_DIR/$target" ]; then
      mv "$SITE_DIR/$target" "$failed_dir/$target"
    fi
    if [ -e "$backup_dir/$target" ]; then
      mv "$backup_dir/$target" "$SITE_DIR/$target"
    fi
  done
  exit 1
fi

rm -f "$ARCHIVE"
printf '%s\n' "$RELEASE_ID" > "$SITE_DIR/.deploy-current"
printf 'Release %s deployed. Backup: %s\n' "$RELEASE_ID" "$backup_dir"
REMOTE
