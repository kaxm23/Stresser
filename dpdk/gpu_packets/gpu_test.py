from numba import cuda
import numpy as np
import time

num_packets = 1_000_000
packet_size = 64

@cuda.jit
def generate_packets(buffer, num_packets, packet_size):
    idx = cuda.grid(1)
    if idx < num_packets:
        start = idx * packet_size
        for i in range(packet_size):
            buffer[start + i] = (idx + i) % 256


buffer = cuda.device_array(num_packets * packet_size, dtype=np.uint8)

threads = 256
blocks = (num_packets + threads - 1) // threads

start = time.time()

generate_packets[blocks, threads](buffer, num_packets, packet_size)
cuda.synchronize()

# GPU → CPU copy
host_buf = buffer.copy_to_host()

end = time.time()

print("GPU generation time:", end - start)
print("Throughput MB/s:", (len(host_buf) / (1024*1024)) / (end - start))