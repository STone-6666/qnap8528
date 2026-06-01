# API 文档

- `GET /api/status`：获取温度、风扇 RPM/PWM、告警、模式
- `POST /api/fan/manual`：设置手动风扇
  - body: `{ "channel": 1, "percent": 50 }`
- `POST /api/fan/auto`：通道切换自动
  - body: `{ "channel": 1 }`
- `POST /api/mode`：全局模式切换
  - body: `{ "mode": "auto|manual" }`
- `GET /api/curves`：列出曲线
- `GET /api/curves/{name}`：读取曲线
- `POST /api/curves/{name}`：保存曲线
- `POST /api/curves/apply`：应用曲线
  - body: `{ "name": "balanced" }`
