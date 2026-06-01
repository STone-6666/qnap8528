# 风扇曲线说明

曲线 JSON 结构：

```json
{
  "name": "balanced",
  "points": [
    {"temp": 30, "pwm": 30},
    {"temp": 45, "pwm": 45}
  ]
}
```

- `temp`：温度（摄氏度）
- `pwm`：风扇百分比（0-100）

系统内置 `silent`、`balanced`、`performance`、`custom`。
