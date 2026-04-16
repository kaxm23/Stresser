import requests
import sys

def test(proxy):
    try:
        r = requests.get("http://httpbin.org/ip", proxies={"http": proxy, "https": proxy}, timeout=5)
        if r.status_code == 200:
            print(proxy)
    except:
        pass

if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        for line in f:
            test(line.strip())
