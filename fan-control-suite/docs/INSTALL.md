# 安装指南

## 通用准备
1. 安装并加载 qnap8528 内核模块
2. 安装 Python 3（可执行 `scripts/install-deps.sh`）

## 直接部署
1. 复制 `backend/`, `frontend/`, `config/`, `systemd/` 到目标系统
2. 将 `config/fan-control.conf` 放到 `/etc/fan-control-suite/`
3. 执行：
   - `cp systemd/fan-control-daemon.service /etc/systemd/system/`
   - `systemctl daemon-reload`
   - `systemctl enable --now fan-control-daemon.service`

## fnOS 打包
- 执行 `scripts/build-fnos.sh`，生成 `dist/*.ipk`

## Synology 打包
- 执行 `scripts/build-synology.sh`，生成 `dist/*.spk`
