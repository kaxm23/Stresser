import requests
import sys

proxy = sys.argv[1]
proxies = {"http": proxy, "https": proxy}

try:
    r = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
    print(f"[✓] {proxy} → {r.json()['origin']}")
except Exception as e:
    print(f"[✗] {proxy} → {e}")
