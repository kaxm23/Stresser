"""Python wrapper for GPU packet generator."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

try:
    import gpu_streamer
    GPU_AVAILABLE = True
except ImportError as e:
    gpu_streamer = None
    GPU_AVAILABLE = False
    _import_error = str(e)


class GpuFloodWrapper:
    """Python interface to Rust GPU packet generator."""

    def __init__(self):
        if not GPU_AVAILABLE:
            raise RuntimeError(f"GPU library not available: {_import_error}")
        self._engine = gpu_streamer.GpuPacketStreamer()
        self._running = False

    def generate_and_copy(self, num_packets: int, packet_size: int):
        """Generate packets on GPU and copy to CPU."""
        return self._engine.generate_and_copy(num_packets, packet_size)

    def send_packets(self, target_ip: str, target_port: int) -> int:
        """Send generated packets via UDP."""
        return self._engine.send_packets(target_ip, target_port)

    def get_cpu_buffer(self):
        return self._engine.get_cpu_buffer()

    def benchmark(self, num_packets: int, packet_size: int) -> float:
        return self._engine.benchmark(num_packets, packet_size)
