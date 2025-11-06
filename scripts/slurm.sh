#!/bin/bash -l
#SBATCH --job-name=qbench
#SBATCH --output=%x-%j.out
#SBATCH --error=%x-%j.err
#
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --exclusive

echo "========================================="
echo "Job started on: $(date)"
echo "Running on node: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo "========================================="

# Load required modules
# module purge
# module load system/CUDA

# Path to your virtual environment
VENV_PATH="${HOME}/environments/qenv"

# Activate virtual environment
echo "Activating virtual environment: ${VENV_PATH}"
source "${VENV_PATH}/bin/activate"

# Verify GPU availability
echo ""
echo "GPU Information:"
nvidia-smi
echo ""

# Verify CUDA and Python setup
echo "Python version:"
python --version
echo ""
echo "Checking Qiskit GPU backend availability:"
python -c "from qiskit_aer import AerSimulator; print('Available devices:', AerSimulator().available_devices())"
echo ""

# Change to project directory
cd "${HOME}/qbench" || exit 1

# Run benchmark with configurable parameters
echo "========================================="
echo "Starting benchmark..."
echo "========================================="

# Run benchmark - customize arguments as needed
python benchmark.py \
    --max-qubits 30 \
    --min-qubits 2 \
    --step 2 \
    --depth 10 \
    --precision double \
    --output-dir "./results/${SLURM_JOB_ID}" \
    --seed 42

echo ""
echo "========================================="
echo "Job finished on: $(date)"
echo "========================================="

# Deactivate virtual environment
deactivate
