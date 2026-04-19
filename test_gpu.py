import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gpu_streamer/target/release'))

import gpu_streamer

streamer = gpu_streamer.GpuPacketStreamer()

num_packets = 2_000_000
packet_size = 64

print("Generating and copying...")
kernel_time, copy_time = streamer.generate_and_copy(num_packets, packet_size)
print(f"Kernel time: {kernel_time*1000:.2f} ms")
print(f"Copy time:   {copy_time*1000:.2f} ms")

throughput = streamer.benchmark(num_packets, packet_size)
print(f"Throughput:  {throughput:.2f} Gbps")
