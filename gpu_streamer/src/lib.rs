use cudarc::driver::{CudaDevice, LaunchConfig, LaunchAsync};
use cudarc::nvrtc::Ptx;
use pyo3::prelude::*;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

#[pyclass]
pub struct GpuPacketStreamer {
    device: Arc<CudaDevice>, // CudaDevice::new returns Arc already
    packet_size: usize,
    num_packets: usize,
    cpu_buffer: Vec<u8>,
}

#[pymethods]
impl GpuPacketStreamer {
    #[new]
    fn new() -> PyResult<Self> {
        let dev = CudaDevice::new(0)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        Ok(GpuPacketStreamer {
            device: dev,
            packet_size: 64,
            num_packets: 0,
            cpu_buffer: Vec::new(),
        })
    }

    fn generate_and_copy(
        &mut self,
        num_packets: usize,
        packet_size: usize,
    ) -> PyResult<(f64, f64)> {
        self.num_packets = num_packets;
        self.packet_size = packet_size;
        let total_bytes = num_packets * packet_size;

        let mut gpu_buf = unsafe { self.device.alloc::<u8>(total_bytes) }
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

        let ptx_src = include_str!("../kernels/packet_gen.ptx");
        let ptx = Ptx::from_src(ptx_src);
        self.device
            .load_ptx(ptx, "packet_gen", &["fill_packets"])
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        let kernel = self
            .device
            .get_func("packet_gen", "fill_packets")
            .ok_or_else(|| pyo3::exceptions::PyRuntimeError::new_err("Kernel not found"))?;

        let cfg = LaunchConfig::for_num_elems(num_packets as u32);
        let start_kernel = Instant::now();
        unsafe {
            kernel
                .launch(cfg, (&mut gpu_buf, num_packets as i32, packet_size as i32))
                .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        }
        self.device
            .synchronize()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        let kernel_time = start_kernel.elapsed().as_secs_f64();

        self.cpu_buffer.resize(total_bytes, 0);
        let start_copy = Instant::now();
        self.device
            .dtoh_sync_copy_into(&gpu_buf, &mut self.cpu_buffer)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        let copy_time = start_copy.elapsed().as_secs_f64();

        Ok((kernel_time, copy_time))
    }

    fn send_packets(&self, target_ip: String, target_port: u16) -> PyResult<usize> {
        use std::net::UdpSocket;
        let socket = UdpSocket::bind("0.0.0.0:0")
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
        let dest = format!("{}:{}", target_ip, target_port);
        let mut sent_bytes = 0;
        for chunk in self.cpu_buffer.chunks(self.packet_size) {
            if let Ok(n) = socket.send_to(chunk, &dest) {
                sent_bytes += n;
            }
        }
        Ok(sent_bytes / self.packet_size)
    }

    fn get_cpu_buffer(&self) -> PyResult<Vec<u8>> {
        Ok(self.cpu_buffer.clone())
    }

    fn benchmark(&mut self, num_packets: usize, packet_size: usize) -> PyResult<f64> {
        let (kernel_time, copy_time) = self.generate_and_copy(num_packets, packet_size)?;
        let total_time = kernel_time + copy_time;
        let total_bytes = (num_packets * packet_size) as f64;
        let throughput_gbps = (total_bytes * 8.0) / (total_time * 1e9);
        Ok(throughput_gbps)
    }

    /// إرسال الحزم باستخدام خيوط Rust متعددة لتحقيق أقصى أداء
    fn send_packets_fast(
        &self,
        target_ip: String,
        target_port: u16,
        num_threads: usize,
        duration_secs: f64,
    ) -> PyResult<u64> {
        use std::net::UdpSocket;

        let dest = format!("{}:{}", target_ip, target_port);
        let packet_size = self.packet_size;
        let cpu_buf = Arc::new(self.cpu_buffer.clone());
        let total_packets = Arc::new(AtomicU64::new(0));
        let stop_flag = Arc::new(AtomicU64::new(0)); // 0 = run, 1 = stop

        let mut handles = vec![];

        for _ in 0..num_threads {
            let cpu_buf = cpu_buf.clone();
            let dest = dest.clone();
            let total_packets = total_packets.clone();
            let stop_flag = stop_flag.clone();
            let num_packets = self.num_packets;
            let packet_size = packet_size;

            let handle = thread::spawn(move || {
                let socket = UdpSocket::bind("0.0.0.0:0").expect("Failed to bind socket");
                socket.set_nonblocking(false).ok(); // blocking for max speed

                let buf = &cpu_buf;
                let mut idx = 0;
                let mut local_sent = 0u64;

                while stop_flag.load(Ordering::Relaxed) == 0 {
                    let offset = idx * packet_size;
                    let chunk = &buf[offset..offset + packet_size];
                    if let Ok(n) = socket.send_to(chunk, &dest) {
                        if n > 0 {
                            local_sent += 1;
                            if local_sent % 1000 == 0 {
                                total_packets.fetch_add(1000, Ordering::Relaxed);
                            }
                        }
                    }
                    idx += 1;
                    if idx >= num_packets {
                        idx = 0;
                    }
                }
                let rem = local_sent % 1000;
                if rem > 0 {
                    total_packets.fetch_add(rem, Ordering::Relaxed);
                }
            });
            handles.push(handle);
        }

        thread::sleep(Duration::from_secs_f64(duration_secs));
        stop_flag.store(1, Ordering::Relaxed);

        for handle in handles {
            let _ = handle.join();
        }

        Ok(total_packets.load(Ordering::Relaxed))
    }
}

#[pymodule]
fn gpu_streamer(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<GpuPacketStreamer>()?;
    Ok(())
}