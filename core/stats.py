import threading
import time
import sys
from datetime import datetime

class StatsMonitor:
    def __init__(self, attack_instance, interval=1.0, json_output=False):
        self.attack = attack_instance
        self.interval = interval
        self.json_output = json_output
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _monitor(self):
        last_reqs = 0
        last_bytes = 0
        while self.running and not self.attack.stop_event.is_set():
            time.sleep(self.interval)
            with self.attack.lock:
                current_reqs = self.attack.stats["requests"]
                current_bytes = self.attack.stats["bytes_sent"]
                elapsed = time.time() - self.attack.stats["start_time"]

            reqs_diff = current_reqs - last_reqs
            bytes_diff = current_bytes - last_bytes
            pps = reqs_diff / self.interval
            bps = bytes_diff / self.interval

            if self.json_output:
                self._print_json(current_reqs, pps, bps, elapsed)
            else:
                self._print_human(current_reqs, pps, bps, elapsed)

            last_reqs = current_reqs
            last_bytes = current_bytes

    def _print_human(self, total, pps, bps, elapsed):
        bar_length = 20
        progress = min(elapsed / self.attack.duration, 1.0)
        filled = int(bar_length * progress)
        bar = "#" * filled + "-" * (bar_length - filled)

        sys.stdout.write(
            f"\r  [{bar}] {elapsed:5.1f}s  "
            f"PPS: {pps:7.1f}  "
            f"Total: {total:7d}  "
            f"BPS: {self._format_bytes(bps)}/s  "
            f"ETA: {max(0, self.attack.duration - elapsed):.0f}s    "
        )
        sys.stdout.flush()

    def _print_json(self, total, pps, bps, elapsed):
        import json
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "elapsed": elapsed,
            "total_requests": total,
            "pps": pps,
            "bps": bps,
            "target": self.attack.target,
            "port": self.attack.port,
            "method": self.attack.__class__.__name__
        }
        print(json.dumps(data))

    @staticmethod
    def _format_bytes(b):
        for unit in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.1f}{unit}"
            b /= 1024
        return f"{b:.1f}TB"
