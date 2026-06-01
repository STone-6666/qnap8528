#!/usr/bin/env sh
set -e
if command -v systemctl >/dev/null 2>&1; then
  cp /opt/fan-control-suite/systemd/fan-control-daemon.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl enable --now fan-control-daemon.service || true
fi
