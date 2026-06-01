#!/usr/bin/env bash
set -euo pipefail

if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  apt-get install -y python3
elif command -v opkg >/dev/null 2>&1; then
  opkg update
  opkg install python3
else
  echo "Please install Python 3 manually" >&2
fi
