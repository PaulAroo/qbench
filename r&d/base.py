from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit.circuit.random import random_circuit
from qiskit.visualization import circuit_drawer
import time
import numpy as np

# --- Parameters ---
n_qubits = 2
depth = 10
seed = 42

# --- Generate random circuit (recommended) ---
qc = random_circuit(n_qubits, depth, measure=False, seed=seed)
basis_gates = ['x', 'y', 'z', 'h', 's', 't', 'cx', 'rx', 'ry', 'rz']
qc_transpiled = transpile(qc, basis_gates=basis_gates)
qc_transpiled.save_statevector()

# print("Generated random circuit:")
# print(qc_transpiled)
# circuit_drawer(qc_transpiled).show()

# --- Initialize simulators ---
sim_cpu = AerSimulator(method="statevector", device="CPU")
sim_gpu = AerSimulator(method="statevector", device="GPU")

# --- Benchmark function ---
def benchmark(simulator, circuit):
  start = time.time()
  job = simulator.run(circuit)
  result = job.result()
  end = time.time()
  return result.get_statevector(circuit), end - start

# --- Run on CPU ---
state_cpu, time_cpu = benchmark(sim_cpu, qc_transpiled)
print(f"CPU simulation time: {time_cpu:.4f} s")

# --- Run on GPU (if available) ---
try:
  state_gpu, time_gpu = benchmark(sim_gpu, qc_transpiled)
  print(f"GPU simulation time: {time_gpu:.4f} s")
except Exception as e:
  print("GPU simulation not available:", e)

# --- Verify equivalence ---
print("State difference:", np.linalg.norm(state_cpu - state_gpu))