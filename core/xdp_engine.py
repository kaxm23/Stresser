"""Wrapper for Rust XDP flood engine."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

try:
    import rust_xdp
    XDP_AVAILABLE = True
except ImportError as e:
    rust_xdp = None
    XDP_AVAILABLE = False
    _import_error = str(e)


class XdpFloodWrapper:
    """Python interface to Rust XDP flood engine."""

    def __init__(
        self,
        interface="eth0",
        dst_mac=None,
        src_mac=None,
        dst_ip=None,
        src_ip=None,
        dst_port=80,
        src_port=12345,
    ):
        if not XDP_AVAILABLE:
            raise RuntimeError(f"Rust XDP library not available: {_import_error}")

        self.interface = interface
        self.dst_mac = dst_mac or [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
        self.src_mac = src_mac or self._get_interface_mac(interface)
        self.dst_ip = dst_ip or [192, 168, 1, 100]
        self.src_ip = src_ip or self._get_interface_ip(interface)
        self.dst_port = dst_port
        self.src_port = src_port

        # Create the actual Rust engine instance
        self._engine = rust_xdp.XdpFlood()
        self._running = False

    def _get_interface_mac(self, iface):
        """Read MAC address from /sys/class/net/<iface>/address."""
        try:
            with open(f"/sys/class/net/{iface}/address", "r") as f:
                mac_str = f.read().strip()
                return [int(x, 16) for x in mac_str.split(":")]
        except Exception:
            return [0x00] * 6

    def _get_interface_ip(self, iface):
        """Get the first IPv4 address of the interface."""
        try:
            import socket
            import fcntl
            import struct

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ifreq = struct.pack("16sH14s", iface[:15].encode(), socket.AF_INET, b"")
            res = fcntl.ioctl(sock, 0x8915, ifreq)  # SIOCGIFADDR
            ip = struct.unpack("16sH2x4s8x", res)[2]
            return list(ip)
        except Exception:
            return [192, 168, 1, 1]

    def start(self):
        """Start the XDP flood."""
        self._engine.start(
            self.interface,
            self.dst_mac,
            self.src_mac,
            self.dst_ip,
            self.src_ip,
            self.dst_port,
            self.src_port,
        )
        self._running = True

    def stop(self):
        """Stop the XDP flood."""
        if self._running:
            self._engine.stop()
            self._running = False

    def get_packets_sent(self):
        """Return the total number of packets sent."""
        return self._engine.get_packets_sent()

    def __del__(self):
        self.stop()
