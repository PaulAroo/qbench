#!/usr/bin/env python3
"""
qbench - Quantum Circuit Simulation Benchmarking
GPU-accelerated performance analysis for Qiskit Aer
"""

import argparse
import time
import os
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for HPC
import matplotlib.pyplot as plt
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit.circuit.random import random_circuit


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Benchmark quantum circuit simulations on CPU and GPU',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Circuit parameters
    parser.add_argument(
        '--min-qubits', 
        type=int, 
        default=2,
        help='Minimum number of qubits'
    )
    parser.add_argument(
        '--max-qubits', 
        type=int, 
        default=24,
        help='Maximum number of qubits'
    )
    parser.add_argument(
        '--step', 
        type=int, 
        default=2,
        help='Step size for qubit range'
    )
    parser.add_argument(
        '--depth', 
        type=int, 
        default=10,
        help='Circuit depth (number of layers)'
    )
    parser.add_argument(
        '--seed', 
        type=int, 
        default=42,
        help='Random seed for reproducibility'
    )
    
    # Backend configuration
    parser.add_argument(
        '--precision', 
        type=str, 
        choices=['single', 'double'], 
        default='double',
        help='Floating point precision'
    )
    parser.add_argument(
        '--backends',
        type=str,
        nargs='+',
        choices=['cpu', 'gpu_default', 'gpu_custatevec', 'all'],
        default=['all'],
        help='Backends to benchmark'
    )
    
    # Output configuration
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default='./results',
        help='Directory for output files'
    )
    parser.add_argument(
        '--save-data', 
        action='store_true',
        help='Save raw benchmark data as CSV'
    )
    parser.add_argument(
        '--no-plots', 
        action='store_true',
        help='Skip plot generation'
    )
    
    # Performance options
    parser.add_argument(
        '--warmup', 
        action='store_true',
        help='Perform warmup run before benchmarking'
    )
    parser.add_argument(
        '--repeats', 
        type=int, 
        default=1,
        help='Number of repetitions per circuit size'
    )
    
    return parser.parse_args()


def setup_backends(precision, backend_list):
    """Initialize simulation backends"""
    backends = {}

    if 'all' in backend_list or 'cpu' in backend_list:
        backends['cpu'] = AerSimulator(
            method="statevector", 
            device="CPU", 
            precision=precision
        )
        print(f"✓ CPU backend initialized (precision: {precision})")
    
    if 'all' in backend_list or 'gpu_default' in backend_list:
        try:
            backends['gpu_default'] = AerSimulator(
                method="statevector", 
                device="GPU", 
                precision=precision,
                cuStateVec_enable=False
            )
            print(f"✓ GPU default backend initialized (precision: {precision})")
        except Exception as e:
            print(f"⚠ Warning: GPU default backend failed: {e}")
    
    if 'all' in backend_list or 'gpu_custatevec' in backend_list:
        try:
            backends['gpu_custatevec'] = AerSimulator(
                method="statevector", 
                device="GPU", 
                precision=precision,
                cuStateVec_enable=True
            )
            print(f"✓ GPU cuStateVec backend initialized (precision: {precision})")
        except Exception as e:
            print(f"⚠ Warning: GPU cuStateVec backend failed: {e}")
    
    return backends


def benchmark(simulator, circuit, repeats=1):
    """Benchmark a single circuit execution"""
    times = []
    for _ in range(repeats):
        start = time.time()
        job = simulator.run(circuit)
        result = job.result()
        end = time.time()
        times.append(end - start)
    
    return np.mean(times), np.std(times)


def run_benchmarks(args):
    """Main benchmark execution"""
    # Setup
    print("\n" + "="*60)
    print("qbench - Quantum Circuit Simulation Benchmarking")
    print("="*60)
    print(f"\nConfiguration:")
    print(f"  Qubit range: {args.min_qubits} to {args.max_qubits} (step {args.step})")
    print(f"  Circuit depth: {args.depth}")
    print(f"  Precision: {args.precision}")
    print(f"  Seed: {args.seed}")
    print(f"  Repeats: {args.repeats}")
    print(f"  Output: {args.output_dir}")
    print()
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize backends
    backends = setup_backends(args.precision, args.backends)
    if not backends:
        print("Error: No backends available!")
        sys.exit(1)
    
    # Setup benchmark parameters
    qubit_sizes = range(args.min_qubits, args.max_qubits + 1, args.step)
    basis_gates = ['x', 'y', 'z', 'h', 's', 't', 'cx', 'rx', 'ry', 'rz']
    
    # Store results
    results = {name: {'times': [], 'stds': []} for name in backends.keys()}
    
    # Warmup run
    if args.warmup:
        print("Performing warmup run...")
        warmup_qc = random_circuit(args.min_qubits, args.depth, measure=False, seed=args.seed)
        warmup_qc = transpile(warmup_qc, basis_gates=basis_gates)
        warmup_qc.save_statevector()
        for name, backend in backends.items():
            try:
                benchmark(backend, warmup_qc)
                print(f"  ✓ {name} warmup complete")
            except Exception as e:
                print(f"  ✗ {name} warmup failed: {e}")
        print()
    
    # Main benchmark loop
    print("="*60)
    print("Starting benchmark...")
    print("="*60 + "\n")
    
    for n_qubits in qubit_sizes:
        print(f"Benchmarking {n_qubits} qubits...")
        
        # Generate and transpile circuit
        qc = random_circuit(n_qubits, args.depth, measure=False, seed=args.seed)
        qc_t = transpile(qc, basis_gates=basis_gates)
        qc_t.save_statevector()
        
        # Benchmark each backend
        for name, backend in backends.items():
            try:
                mean_time, std_time = benchmark(backend, qc_t, repeats=args.repeats)
                results[name]['times'].append(mean_time)
                results[name]['stds'].append(std_time)
                
                if args.repeats > 1:
                    print(f"  {name:20s}: {mean_time:8.4f}s ± {std_time:.4f}s")
                else:
                    print(f"  {name:20s}: {mean_time:8.4f}s")
            except Exception as e:
                print(f"  {name:20s}: FAILED ({e})")
                results[name]['times'].append(np.nan)
                results[name]['stds'].append(np.nan)
        
        print()
    
    # Save raw data
    if args.save_data:
        save_benchmark_data(results, qubit_sizes, output_path, args)
    
    # Generate plots
    if not args.no_plots:
        generate_plots(results, qubit_sizes, output_path, args)
    
    print("="*60)
    print("Benchmark complete!")
    print(f"Results saved to: {output_path}")
    print("="*60)


def save_benchmark_data(results, qubit_sizes, output_path, args):
    """Save benchmark results to CSV"""
    import csv
    
    csv_file = output_path / 'benchmark_results.csv'
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        headers = ['qubits']
        for name in results.keys():
            headers.extend([f'{name}_time', f'{name}_std'])
        writer.writerow(headers)
        
        # Data
        for i, n_qubits in enumerate(qubit_sizes):
            row = [n_qubits]
            for name in results.keys():
                row.append(results[name]['times'][i])
                row.append(results[name]['stds'][i])
            writer.writerow(row)
    
    print(f"✓ Saved data to {csv_file}")


def generate_plots(results, qubit_sizes, output_path, args):
    """Generate benchmark visualization plots"""
    print("\nGenerating plots...")
    
    # Convert to arrays
    qubit_array = np.array(list(qubit_sizes))
    
    # Two-panel plot: Speedup + Execution Time
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Left: Speedup (if CPU available)
    if 'cpu' in results:
        cpu_times = np.array(results['cpu']['times'])
        
        for name, data in results.items():
            if name != 'cpu':
                times = np.array(data['times'])
                speedup = cpu_times / times
                ax1.plot(qubit_array, speedup, 'o-', label=f'{name} vs CPU', 
                        linewidth=2, markersize=6)
        
        ax1.axhline(1, color='red', linestyle='--', linewidth=2, alpha=0.7, 
                   label='No speedup')
        ax1.set_xlabel("Number of Qubits", fontsize=12)
        ax1.set_ylabel("Speedup Factor (×)", fontsize=12)
        ax1.set_title("GPU Speedup over CPU", fontsize=14, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(qubit_array)
    
    # Right: Execution times (log scale)
    for name, data in results.items():
        times = np.array(data['times'])
        ax2.plot(qubit_array, times, 'o-', label=name, linewidth=2, markersize=6)
    
    ax2.set_xlabel("Number of Qubits", fontsize=12)
    ax2.set_ylabel("Execution Time (seconds)", fontsize=12)
    ax2.set_title("Execution Time Comparison", fontsize=14, fontweight='bold')
    ax2.set_yscale('log')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(qubit_array)
    
    plt.tight_layout()
    
    plot_file = output_path / 'benchmark_comparison.png'
    plt.savefig(plot_file, dpi=300, bbox_inches='tight')
    plt.savefig(output_path / 'benchmark_comparison.pdf', bbox_inches='tight')
    print(f"✓ Saved plot to {plot_file}")
    
    plt.close()


def main():
  """Entry point"""
  args = parse_arguments()
  
  try:
      run_benchmarks(args)
  except KeyboardInterrupt:
      print("\n\nBenchmark interrupted by user.")
      sys.exit(1)
  except Exception as e:
      print(f"\n\nError: {e}")
      import traceback
      traceback.print_exc()
      sys.exit(1)


if __name__ == '__main__':
    main()
