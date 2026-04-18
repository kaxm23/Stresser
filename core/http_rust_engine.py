"""Python wrapper for Rust HTTP flood engine."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

try:
    import rust_http
    RUST_HTTP_AVAILABLE = True
except ImportError as e:
    rust_http = None
    RUST_HTTP_AVAILABLE = False
    _import_error = str(e)


class RustHttpFloodWrapper:
    """Python interface to Rust HTTP flood engine."""

    def __init__(
        self,
        url: str,
        concurrency: int = 1000,
        http2: bool = True,
        disable_pooling: bool = False,
    ):
        if not RUST_HTTP_AVAILABLE:
            raise RuntimeError(f"Rust HTTP library not available: {_import_error}")
        self.url = url
        self.concurrency = concurrency
        self.http2 = http2
        self.disable_pooling = disable_pooling
        self._engine = rust_http.HttpFlood()
        self._running = False

    def start(self):
        self._engine.start(
            self.url,
            self.concurrency,
            self.http2,
            self.disable_pooling,
        )
        self._running = True

    def stop(self):
        if self._running:
            self._engine.stop()
            self._running = False

    def get_requests_sent(self) -> int:
        return self._engine.get_requests_sent()

    def __del__(self):
        self.stop()