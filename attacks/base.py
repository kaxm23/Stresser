import threading
import time
from abc import ABC, abstractmethod

class AttackBase(ABC):
    def __init__(self, target: str, port: int, threads: int, duration: int,
                 rps: int = 0, proxy_manager=None, **kwargs):
        self.target = target
        self.port = port
        self.thread_count = threads
        self.duration = duration
        self.rps_limit = rps
        self.proxy_manager = proxy_manager
        self.kwargs = kwargs

        self.stop_event = threading.Event()
        self.stats = {
            "requests": 0,
            "bytes_sent": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
        self.lock = threading.Lock()

    def worker(self) -> int:
        """Override this for simple synchronous attacks."""
        raise NotImplementedError("worker() must be implemented by synchronous attacks")

    def _worker_loop(self):
        if self.rps_limit > 0:
            interval = 1.0 / (self.rps_limit / self.thread_count)
        else:
            interval = 0
        last_send = time.time()
        while not self.stop_event.is_set():
            if interval > 0:
                elapsed = time.time() - last_send
                if elapsed < interval:
                    time.sleep(interval - elapsed)
                last_send = time.time()
            try:
                sent = self.worker()
                with self.lock:
                    self.stats["requests"] += 1
                    self.stats["bytes_sent"] += sent
            except Exception:
                with self.lock:
                    self.stats["errors"] += 1

    def start(self):
        self.stats["start_time"] = time.time()
        threads = []
        for _ in range(self.thread_count):
            t = threading.Thread(target=self._worker_loop)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(self.duration)
        self.stop_event.set()

        for t in threads:
            t.join(timeout=1)

        self.stats["end_time"] = time.time()
        return self.stats
