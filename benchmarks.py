import time
import numpy as np
import matplotlib.pyplot as plt
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit.circuit.random import random_circuit

# --- Parameters ---
depth = 10
seed = 42
qubit_sizes = range(2, 25, 2)
basis_gates = ['x', 'y', 'z', 'h', 's', 't', 'cx', 'rx', 'ry', 'rz']

# --- Three Simulators ---
sim_cpu = AerSimulator(method="statevector", device="CPU")
sim_gpu_default = AerSimulator(method="statevector", device="GPU", cuStateVec_enable=False)
sim_gpu_custatevec = AerSimulator(method="statevector", device="GPU", cuStateVec_enable=True)

# --- Benchmark helper ---
def benchmark(simulator, circuit):
  start = time.time()
  job = simulator.run(circuit)
  result = job.result()
  end = time.time()
  return end - start

cpu_times, gpu_default_times, gpu_custatevec_times = [], [], []

for n_qubits in qubit_sizes:
  qc = random_circuit(n_qubits, depth, measure=False, seed=seed)
  qc_t = transpile(qc, basis_gates=basis_gates)
  qc_t.save_statevector()
  print(f"Running {n_qubits}-qubit circuit...")

  # CPU benchmark
  t_cpu = benchmark(sim_cpu, qc_t)
  cpu_times.append(t_cpu)
  print(f"  CPU: {t_cpu:.4f}s")

  # GPU default benchmark
  try:
      t_gpu_default = benchmark(sim_gpu_default, qc_t)
      print(f"  GPU (default): {t_gpu_default:.4f}s")
  except Exception as e:
      print(f"  GPU (default) failed:", e)
      t_gpu_default = np.nan
  gpu_default_times.append(t_gpu_default)

  # GPU cuStateVec benchmark
  try:
    t_gpu_custatevec = benchmark(sim_gpu_custatevec, qc_t)
    print(f"  GPU (cuStateVec): {t_gpu_custatevec:.4f}s")
  except Exception as e:
    print(f"  GPU (cuStateVec) failed:", e)
    t_gpu_custatevec = np.nan
  gpu_custatevec_times.append(t_gpu_custatevec)


# --- Compute speedups ---
speedup_default = np.array(cpu_times) / np.array(gpu_default_times)
speedup_custatevec = np.array(cpu_times) / np.array(gpu_custatevec_times)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Left: Speedup comparison
ax1.plot(qubit_sizes, speedup_default, 's-', label='GPU Default vs CPU', 
         linewidth=2, markersize=6, color='tab:orange')
ax1.plot(qubit_sizes, speedup_custatevec, '^-', label='GPU cuStateVec vs CPU', 
         linewidth=2, markersize=6, color='tab:green')
ax1.axhline(1, color='red', linestyle='--', linewidth=2, alpha=0.7, label='No speedup')
ax1.set_xlabel("Number of Qubits", fontsize=12)
ax1.set_ylabel("Speedup Factor (×)", fontsize=12)
ax1.set_title("GPU Speedup over CPU", fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xticks(qubit_sizes)

# Right: Execution times (log scale)
ax2.plot(qubit_sizes, cpu_times, 'o-', label='CPU', linewidth=2, markersize=6)
ax2.plot(qubit_sizes, gpu_default_times, 's-', label='GPU (default)', linewidth=2, markersize=6)
ax2.plot(qubit_sizes, gpu_custatevec_times, '^-', label='GPU (cuStateVec)', linewidth=2, markersize=6)
ax2.set_xlabel("Number of Qubits", fontsize=12)
ax2.set_ylabel("Execution Time (seconds)", fontsize=12)
ax2.set_title("Execution Time Comparison", fontsize=14, fontweight='bold')
ax2.set_yscale('log')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xticks(qubit_sizes)

plt.tight_layout()
plt.savefig('three_backend_comparison.png', dpi=300, bbox_inches='tight')
