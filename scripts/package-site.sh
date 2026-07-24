#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
archive="$project_dir/fitstudy-site.tar.gz"
temporary_archive="$(mktemp "${TMPDIR:-/tmp}/fitstudy-site.XXXXXX.tar.gz")"

cleanup() {
  rm -f "$temporary_archive"
}
trap cleanup EXIT

cd "$project_dir"
tar -czf "$temporary_archive" \
  index.html \
  app.js \
  styles.css \
  fitness_syllabus.md \
  reviews.json \
  progress.json \
  html \
  home \
  library
gzip -t "$temporary_archive"
mv "$temporary_archive" "$archive"
trap - EXIT

printf 'Package ready: %s\n' "$archive"
