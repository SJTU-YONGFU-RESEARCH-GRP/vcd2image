#!/bin/bash
# VCD2Image Testing Setup Script
# This script sets up the local environment for testing

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f "README.md" ]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

log_info "Setting up VCD2Image testing environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
log_info "Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        log_error "Failed to create virtual environment"
        exit 1
    fi
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    log_error "Failed to activate virtual environment"
    exit 1
fi
log_success "Virtual environment activated"

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip
if [ $? -ne 0 ]; then
    log_warning "Failed to upgrade pip, continuing..."
fi

# Install the package in development mode with all optional dependencies
log_info "Installing VCD2Image with development and rendering dependencies..."
pip install -e ".[dev,rendering]"
if [ $? -ne 0 ]; then
    log_error "Failed to install dependencies"
    log_info "Try installing dependencies manually:"
    log_info "  pip install -e \".\""
    log_info "  pip install pytest ruff mypy matplotlib numpy"
    exit 1
fi
log_success "Dependencies installed"

# Verify installations
log_info "Verifying tool installations..."

TOOLS=("pytest" "ruff" "mypy")
MISSING_TOOLS=""

for tool in "${TOOLS[@]}"; do
    if command -v $tool &> /dev/null; then
        log_success "$tool is available"
    else
        MISSING_TOOLS="$MISSING_TOOLS $tool"
        log_warning "$tool is not available"
    fi
done

if [ -n "$MISSING_TOOLS" ]; then
    log_warning "Some tools are not available globally:$MISSING_TOOLS"
    log_info "They may be available in the virtual environment only"
fi

# Run a quick test to verify everything works
log_info "Running quick verification test..."
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from vcd2image.core.models import SignalDef
    print('✓ Core imports work')
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)

try:
    import matplotlib
    print('✓ Matplotlib available')
except ImportError:
    print('⚠ Matplotlib not available (optional for basic functionality)')

print('✓ Basic verification passed')
"

if [ $? -eq 0 ]; then
    log_success "Setup verification passed"
else
    log_error "Setup verification failed"
    exit 1
fi

# Display next steps
echo ""
log_success "VCD2Image testing environment setup complete!"
echo ""
log_info "Next steps:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run tests: ./scripts/test.sh"
echo "  3. Run specific tests:"
echo "     - Unit tests only: ./scripts/test.sh --unit"
echo "     - Fast mode: ./scripts/test.sh --fast"
echo "     - Lint only: ./scripts/test.sh --lint"
echo "  4. Clean examples: ./scripts/clean.sh examples"
echo ""
log_info "Available test options:"
echo "  --unit     : Run unit tests only"
echo "  --fast     : Run tests quickly (no coverage, stop on failure)"
echo "  --lint     : Run linting only"
echo "  --type     : Run type checking only"
echo "  --format   : Run formatting check only"
echo "  --examples : Run vcd2image examples only"
echo ""
log_info "For more information, see scripts/SCRIPTS.md"
