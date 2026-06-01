import configparser
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "service": {
        "host": "0.0.0.0",
        "port": "8528",
        "poll_interval": "5",
        "auto_load_module": "true",
        "module_name": "qnap8528",
    },
    "paths": {
        "hwmon_root": "/sys/class/hwmon",
        "curve_dir": "/etc/fan-control-suite/curves",
        "lock_file": "/var/run/fan-control-suite.lock",
    },
    "control": {
        "failure_min_rpm": "300",
        "manual_default_percent": "50",
    },
}


def ensure_default_config(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser()
    parser.read_dict(DEFAULT_CONFIG)
    with path.open("w", encoding="utf-8") as fh:
        parser.write(fh)


def load_config(path: str) -> configparser.ConfigParser:
    cfg_path = Path(path)
    ensure_default_config(cfg_path)
    parser = configparser.ConfigParser()
    parser.read_dict(DEFAULT_CONFIG)
    parser.read(cfg_path)
    return parser


def load_curve_file(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)
