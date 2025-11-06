#!/bin/bash
#
# Setup script for qbench virtual environment
# Usage: ./setup_env.sh [path/to/venv]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}qbench - Environment Setup${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""

# Default virtual environment path
DEFAULT_VENV_PATH="${HOME}/environments/qenv"
VENV_PATH="${1:-$DEFAULT_VENV_PATH}"

echo -e "Virtual environment will be created at: ${YELLOW}${VENV_PATH}${NC}"
echo ""

# Check if virtual environment already exists
if [ -d "${VENV_PATH}" ]; then
    echo -e "${YELLOW}Warning: Virtual environment already exists at ${VENV_PATH}${NC}"
    read -p "Do you want to remove it and start fresh? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        rm -rf "${VENV_PATH}"
    else
        echo "Aborting."
        exit 1
    fi
fi

# Load required modules (Iris cluster specific)
echo "Loading required modules..."
module purge
# module load system/CUDA/12.0.0
module load lang/Python

echo -e "${GREEN}✓${NC} Modules loaded"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv "${VENV_PATH}"
echo -e "${GREEN}✓${NC} Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source "${VENV_PATH}/bin/activate"
echo -e "${GREEN}✓${NC} Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}✓${NC} pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."

# Core dependencies
pip install numpy matplotlib

# Qiskit and Aer (GPU version)
pip install qiskit==0.46.3
pip install qiskit-aer-gpu==0.13.3

echo -e "${GREEN}✓${NC} Dependencies installed"
echo ""

# Verify installation
echo "Verifying installation..."
echo ""

echo "Python version:"
python --version
echo ""

echo "Installed packages:"
pip list | grep -E "qiskit|numpy|matplotlib"
echo ""

echo "Testing Qiskit Aer GPU backend:"
python -c "
from qiskit_aer import AerSimulator
sim = AerSimulator()
print('Available devices:', sim.available_devices())
print('Available methods:', sim.available_methods())
" || echo -e "${YELLOW}Warning: GPU backend test failed (may not be available on login node)${NC}"

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "To activate the environment in the future, run:"
echo -e "  ${YELLOW}source ${VENV_PATH}/bin/activate${NC}"
echo ""
echo "To submit a benchmark job:"
echo -e "  ${YELLOW}sbatch run_benchmark.slurm${NC}"
echo ""

# # Create activation helper script
# ACTIVATE_SCRIPT="${HOME}/activate_qbench.sh"
# cat > "${ACTIVATE_SCRIPT}" << EOF
# #!/bin/bash
# # Quick activation script for qbench environment
# source "${VENV_PATH}/bin/activate"
# echo "qbench environment activated"
# EOF
# chmod +x "${ACTIVATE_SCRIPT}"

# echo "Quick activation script created:"
# echo -e "  ${YELLOW}source ~/activate_qbench.sh${NC}"
# echo ""

# deactivate
