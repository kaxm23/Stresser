extern "C" __global__ void fill_packets(unsigned char *buffer, int num_packets, int packet_size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= num_packets) return;
    unsigned char *pkt = buffer + idx * packet_size;
    for (int i = 0; i < packet_size; i++) {
        pkt[i] = (idx + i) % 256;
    }
}