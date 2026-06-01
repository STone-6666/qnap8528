import fcntl
import glob
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FanStatus:
    channel: int
    rpm: int
    pwm_raw: int
    pwm_percent: int
    mode: str
    failed: bool


class HwmonFanController:
    PWM_RAW_MAX = 255

    def __init__(self, hwmon_root: str, lock_file: str, failure_min_rpm: int = 300):
        self.hwmon_root = hwmon_root
        self.lock_file = lock_file
        self.failure_min_rpm = failure_min_rpm

    @contextmanager
    def _file_lock(self):
        Path(self.lock_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.lock_file, "w", encoding="utf-8") as lock_fh:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)

    def _discover_hwmon(self):
        candidates = sorted(glob.glob(os.path.join(self.hwmon_root, "hwmon*")))
        for c in candidates:
            if glob.glob(os.path.join(c, "pwm*")):
                return c
        raise FileNotFoundError(f"No hwmon pwm interface found in {self.hwmon_root}")

    @staticmethod
    def _read_int(path: str, default: int = 0) -> int:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return int(fh.read().strip())
        except (ValueError, OSError):
            return default

    @staticmethod
    def _write_int(path: str, value: int):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"{value}\n")

    def get_temperatures(self):
        hwmon = self._discover_hwmon()
        temps = []
        for tpath in sorted(glob.glob(os.path.join(hwmon, "temp*_input"))):
            value = self._read_int(tpath, default=-1)
            if value >= 0:
                temps.append({
                    "sensor": os.path.basename(tpath).replace("_input", ""),
                    "celsius": round(value / 1000.0, 1),
                })
        return temps

    def get_fan_status(self):
        hwmon = self._discover_hwmon()
        fan_paths = sorted(glob.glob(os.path.join(hwmon, "fan*_input")))
        status = []
        for fan_path in fan_paths:
            fan_name = os.path.basename(fan_path)
            channel = int(fan_name.replace("fan", "").replace("_input", ""))
            pwm_path = os.path.join(hwmon, f"pwm{channel}")
            pwm_enable = os.path.join(hwmon, f"pwm{channel}_enable")
            rpm = self._read_int(fan_path)
            pwm_raw = self._read_int(pwm_path)
            pwm_percent = max(0, min(100, round((pwm_raw / float(self.PWM_RAW_MAX)) * 100)))
            mode_value = self._read_int(pwm_enable, default=2)
            mode = "manual" if mode_value == 1 else "auto"
            failed = pwm_percent > 20 and rpm < self.failure_min_rpm
            status.append(FanStatus(channel, rpm, pwm_raw, pwm_percent, mode, failed).__dict__)
        return status

    def set_manual_percent(self, channel: int, percent: int):
        if percent < 0 or percent > 100:
            raise ValueError("percent must be 0-100")
        hwmon = self._discover_hwmon()
        pwm_path = os.path.join(hwmon, f"pwm{channel}")
        pwm_enable = os.path.join(hwmon, f"pwm{channel}_enable")
        pwm_raw = max(0, min(self.PWM_RAW_MAX, round(percent * self.PWM_RAW_MAX / 100)))
        with self._file_lock():
            self._write_int(pwm_enable, 1)
            self._write_int(pwm_path, pwm_raw)

    def set_auto_mode(self, channel: int):
        hwmon = self._discover_hwmon()
        pwm_enable = os.path.join(hwmon, f"pwm{channel}_enable")
        with self._file_lock():
            self._write_int(pwm_enable, 2)

    def available_channels(self):
        hwmon = self._discover_hwmon()
        channels = []
        for p in sorted(glob.glob(os.path.join(hwmon, "pwm[0-9]*"))):
            name = os.path.basename(p)
            if "_" in name:
                continue
            channels.append(int(name.replace("pwm", "")))
        return channels

    def get_overview(self):
        fans = self.get_fan_status()
        return {
            "temperatures": self.get_temperatures(),
            "fans": fans,
            "alerts": [f"fan{f['channel']} failed" for f in fans if f["failed"]],
        }
