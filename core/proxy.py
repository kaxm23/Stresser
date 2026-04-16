import random
import threading
import subprocess
import time

try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False


class ProxyManager:
    def __init__(self, proxy_file=None, tor_control_port=9051, tor_password=None):
        self.proxies = []
        self.lock = threading.Lock()
        self.index = 0
        self.tor_control_port = tor_control_port
        self.tor_password = tor_password
        self._tor_controller = None
        self._tor_lock = threading.Lock()
        if proxy_file:
            self.load(proxy_file)

    def load(self, path):
        with open(path, "r") as f:
            self.proxies = [line.strip() for line in f if line.strip()]

    def get_next(self):
        with self.lock:
            if not self.proxies:
                return None
            proxy = self.proxies[self.index % len(self.proxies)]
            self.index += 1
            return proxy

    def get_random(self):
        with self.lock:
            if not self.proxies:
                return None
            return random.choice(self.proxies)

    def format_requests(self, proxy_str):
        if proxy_str.startswith("socks"):
            return {"http": proxy_str, "https": proxy_str}
        return {"http": proxy_str, "https": proxy_str}

    def rotate_tor_circuit(self):
        """Request a new Tor circuit (new exit node)."""
        if STEM_AVAILABLE:
            return self._rotate_with_stem()
        else:
            return self._rotate_with_signal()

    def _rotate_with_stem(self):
        with self._tor_lock:
            try:
                if not self._tor_controller:
                    self._tor_controller = Controller.from_port(port=self.tor_control_port)
                    if self.tor_password:
                        self._tor_controller.authenticate(password=self.tor_password)
                    else:
                        self._tor_controller.authenticate()
                self._tor_controller.signal(Signal.NEWNYM)
                return True
            except Exception as e:
                print(f"[!] Tor rotation failed: {e}")
                return False

    def _rotate_with_signal(self):
        """Fallback: send SIGHUP to tor process (less reliable)."""
        try:
            subprocess.run(["pkill", "-HUP", "tor"], check=True)
            time.sleep(2)  # Give Tor time to establish new circuit
            return True
        except Exception as e:
            print(f"[!] SIGHUP rotation failed: {e}")
            return False

    def close(self):
        if self._tor_controller:
            self._tor_controller.close()