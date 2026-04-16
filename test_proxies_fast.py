import requests
import threading
import sys
from queue import Queue

def test_proxy(proxy, working_set):
    proxies = {"http": proxy, "https": proxy}
    try:
        r = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=3)
        if r.status_code == 200:
            working_set.append(proxy)
            print(f"[+] {proxy}")
    except:
        pass

def worker(q, working):
    while not q.empty():
        proxy = q.get()
        test_proxy(proxy, working)
        q.task_done()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} proxies.txt")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        proxies = [line.strip() for line in f if line.strip()]

    q = Queue()
    for p in proxies:
        q.put(p)

    working = []
    threads = []
    for _ in range(50):  # 50 concurrent checks
        t = threading.Thread(target=worker, args=(q, working))
        t.start()
        threads.append(t)

    q.join()
    for t in threads:
        t.join()

    with open("working_proxies.txt", "w") as out:
        for p in working:
            out.write(p + "\n")

    print(f"\n[✓] {len(working)} working proxies saved to working_proxies.txt")