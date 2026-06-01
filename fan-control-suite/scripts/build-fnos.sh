#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/.build/fnos"
PKG_NAME="fan-control-suite"
VERSION="1.0.0"
ARCH="x86_64"

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/control" "${BUILD_DIR}/data/opt/${PKG_NAME}" "${BUILD_DIR}/data/etc/fan-control-suite"

cp "${ROOT_DIR}/package/fnos/CONTROL" "${BUILD_DIR}/control/control"
for script in "${ROOT_DIR}/package/fnos/"*.sh; do
  [ -e "${script}" ] || continue
  cp "${script}" "${BUILD_DIR}/control/"
done
for script in "${BUILD_DIR}/control/"*.sh; do
  [ -e "${script}" ] || continue
  chmod +x "${script}"
done

cp -r "${ROOT_DIR}/backend" "${BUILD_DIR}/data/opt/${PKG_NAME}/"
cp -r "${ROOT_DIR}/frontend" "${BUILD_DIR}/data/opt/${PKG_NAME}/"
cp -r "${ROOT_DIR}/systemd" "${BUILD_DIR}/data/opt/${PKG_NAME}/"
cp -r "${ROOT_DIR}/config/curves" "${BUILD_DIR}/data/etc/fan-control-suite/"
cp "${ROOT_DIR}/config/fan-control.conf" "${BUILD_DIR}/data/etc/fan-control-suite/"

mkdir -p "${ROOT_DIR}/dist"
PKG_FILE="${ROOT_DIR}/dist/${PKG_NAME}_${VERSION}_${ARCH}.ipk"
(
  cd "${BUILD_DIR}"
  tar czf control.tar.gz -C control .
  tar czf data.tar.gz -C data .
  echo "2.0" > debian-binary
  tar czf "${PKG_FILE}" debian-binary control.tar.gz data.tar.gz
)

echo "Created ${PKG_FILE}"
