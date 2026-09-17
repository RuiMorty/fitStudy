#!/bin/sh
set -eu
case "${1:-}" in
  *assword*)
    exec /usr/bin/security find-generic-password \
      -a "$FITSTUDY_KEYCHAIN_ACCOUNT" -s "$FITSTUDY_KEYCHAIN_SERVICE" -w
    ;;
  *) exit 1 ;;
esac
