import json
from pathlib import Path


class CurveManager:
    DEFAULT_PWM = 40

    def __init__(self, curve_dir: str):
        self.curve_dir = Path(curve_dir)
        self.curve_dir.mkdir(parents=True, exist_ok=True)

    def list_curves(self):
        return sorted([p.stem for p in self.curve_dir.glob("*.json")])

    def load_curve(self, name: str):
        path = self.curve_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"curve '{name}' not found")
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def save_curve(self, name: str, data: dict):
        if "points" not in data or not isinstance(data["points"], list):
            raise ValueError("curve data must include points[]")
        for point in data["points"]:
            if not isinstance(point, dict) or "temp" not in point or "pwm" not in point:
                raise ValueError("each point must include temp and pwm")
            try:
                temp = float(point["temp"])
                pwm = float(point["pwm"])
            except (TypeError, ValueError) as exc:
                raise ValueError("temp and pwm must be numeric") from exc
            if temp < 0 or temp > 120:
                raise ValueError("temp must be between 0 and 120")
            if pwm < 0 or pwm > 100:
                raise ValueError("pwm must be between 0 and 100")
        path = self.curve_dir / f"{name}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)

    @staticmethod
    def interpolate_pwm(temp_c: float, points):
        if not points:
            return CurveManager.DEFAULT_PWM
        points = sorted(points, key=lambda p: p["temp"])
        if temp_c <= points[0]["temp"]:
            return points[0]["pwm"]
        if temp_c >= points[-1]["temp"]:
            return points[-1]["pwm"]
        for idx in range(len(points) - 1):
            a = points[idx]
            b = points[idx + 1]
            if a["temp"] <= temp_c <= b["temp"]:
                ratio = (temp_c - a["temp"]) / (b["temp"] - a["temp"])
                return round(a["pwm"] + (b["pwm"] - a["pwm"]) * ratio)
        return points[-1]["pwm"]
