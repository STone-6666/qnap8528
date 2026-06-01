#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/.build/synology"
PKG_NAME="fan-control-suite"
VERSION="1.0.0"

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/package" "${BUILD_DIR}/scripts" "${BUILD_DIR}/conf"

cp "${ROOT_DIR}/package/synology/INFO" "${BUILD_DIR}/INFO"
for script in "${ROOT_DIR}/package/synology/scripts/"*; do
  [ -e "${script}" ] || continue
  cp "${script}" "${BUILD_DIR}/scripts/"
done
chmod +x "${BUILD_DIR}/scripts/"*

cp -r "${ROOT_DIR}/backend" "${BUILD_DIR}/package/"
cp -r "${ROOT_DIR}/frontend" "${BUILD_DIR}/package/"
cp -r "${ROOT_DIR}/systemd" "${BUILD_DIR}/package/"
cp -r "${ROOT_DIR}/config" "${BUILD_DIR}/package/"
cp -r "${ROOT_DIR}/package/synology/ui" "${BUILD_DIR}/package/"

mkdir -p "${ROOT_DIR}/dist"
PKG_FILE="${ROOT_DIR}/dist/${PKG_NAME}-${VERSION}.spk"
(
  cd "${BUILD_DIR}"
  tar czf package.tgz -C package .
  tar czf "${PKG_FILE}" INFO scripts package.tgz
)

echo "Created ${PKG_FILE}"
