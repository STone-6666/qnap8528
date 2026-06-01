#!/usr/bin/env python3
import argparse
import json
import logging
import logging.handlers
import os
import subprocess
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from config import load_config
from curve_manager import CurveManager
from fan_control import HwmonFanController


def build_logger():
    logger = logging.getLogger("fan-control-daemon")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(name)s: %(levelname)s %(message)s")
    try:
        handler = logging.handlers.SysLogHandler(address="/dev/log")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except OSError:
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        logger.addHandler(stream)
    return logger


class FanService:
    def __init__(self, cfg):
        self.cfg = cfg
        self.logger = build_logger()
        self.controller = HwmonFanController(
            cfg.get("paths", "hwmon_root"),
            cfg.get("paths", "lock_file"),
            cfg.getint("control", "failure_min_rpm"),
        )
        self.curves = CurveManager(cfg.get("paths", "curve_dir"))
        self.mode = "auto"
        self.active_curve = "balanced"
        self.running = True

    def preload_module(self):
        if not self.cfg.getboolean("service", "auto_load_module"):
            return
        module_name = self.cfg.get("service", "module_name")
        try:
            subprocess.run(["modprobe", module_name], check=True, capture_output=True)
            self.logger.info("loaded kernel module %s", module_name)
        except Exception as exc:
            self.logger.warning("unable to load module %s: %s", module_name, exc)

    def auto_loop(self):
        while self.running:
            if self.mode == "auto":
                try:
                    status = self.controller.get_overview()
                    temps = status["temperatures"]
                    if temps:
                        max_temp = max(t["celsius"] for t in temps)
                        curve = self.curves.load_curve(self.active_curve)
                        pwm = self.curves.interpolate_pwm(max_temp, curve["points"])
                        for ch in self.controller.available_channels():
                            self.controller.set_manual_percent(ch, pwm)
                    for alert in status["alerts"]:
                        self.logger.error(alert)
                except Exception as exc:
                    self.logger.error("auto loop failed: %s", exc)
            time.sleep(self.cfg.getint("service", "poll_interval"))


class Handler(BaseHTTPRequestHandler):
    service = None

    def _json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _require_root(self):
        if os.geteuid() != 0:
            self._json({"error": "root privileges required"}, status=HTTPStatus.FORBIDDEN)
            return False
        return True

    def do_GET(self):
        if self.path == "/api/status":
            s = self.service
            overview = s.controller.get_overview()
            overview["mode"] = s.mode
            overview["active_curve"] = s.active_curve
            self._json(overview)
            return
        if self.path == "/api/curves":
            self._json({"curves": self.service.curves.list_curves()})
            return
        if self.path.startswith("/api/curves/"):
            name = self.path.split("/")[-1]
            try:
                self._json(self.service.curves.load_curve(name))
            except Exception as exc:
                self._json({"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
            return
        self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self):
        if not self._require_root():
            return
        data = self._parse()
        s = self.service

        if self.path == "/api/fan/manual":
            s.controller.set_manual_percent(int(data["channel"]), int(data["percent"]))
            s.mode = "manual"
            self._json({"ok": True})
            return

        if self.path == "/api/fan/auto":
            s.controller.set_auto_mode(int(data["channel"]))
            s.mode = "auto"
            self._json({"ok": True})
            return

        if self.path == "/api/mode":
            mode = data.get("mode", "auto")
            if mode not in {"auto", "manual"}:
                self._json({"error": "invalid mode"}, status=HTTPStatus.BAD_REQUEST)
                return
            s.mode = mode
            self._json({"ok": True, "mode": s.mode})
            return

        if self.path == "/api/curves/apply":
            name = data["name"]
            s.curves.load_curve(name)
            s.active_curve = name
            s.mode = "auto"
            self._json({"ok": True})
            return

        if self.path.startswith("/api/curves/"):
            name = self.path.split("/")[-1]
            s.curves.save_curve(name, data)
            self._json({"ok": True})
            return

        self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


def main():
    parser = argparse.ArgumentParser(description="Fan control daemon")
    parser.add_argument("--config", default="/etc/fan-control-suite/fan-control.conf")
    args = parser.parse_args()

    cfg = load_config(args.config)
    service = FanService(cfg)
    service.preload_module()

    Handler.service = service
    host = cfg.get("service", "host")
    port = cfg.getint("service", "port")
    server = ThreadingHTTPServer((host, port), Handler)

    loop_thread = threading.Thread(target=service.auto_loop, daemon=True)
    loop_thread.start()

    try:
        service.logger.info("fan control daemon listening on %s:%s", host, port)
        server.serve_forever()
    finally:
        service.running = False
        server.server_close()


if __name__ == "__main__":
    main()
