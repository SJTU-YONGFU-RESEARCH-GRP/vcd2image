#!/bin/bash
# VCD2Image Installation Script
# This script sets up the development environment for VCD2Image

set -e  # Exit on any error

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

PROJECT_NAME="VCD2Image"
VENV_DIR="venv"

log_info "Starting installation of $PROJECT_NAME..."

# Check Python version
log_info "Checking Python version..."
if ! command -v python &> /dev/null; then
    log_error "Python is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    log_error "Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

log_success "Python $PYTHON_VERSION found ✓"

# Create virtual environment
log_info "Creating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    log_warning "Virtual environment already exists at $VENV_DIR"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        log_info "Removed existing virtual environment"
    else
        log_info "Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    python -m venv "$VENV_DIR"
    log_success "Virtual environment created ✓"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip

# Install the package in development mode
log_info "Installing $PROJECT_NAME in development mode..."
pip install -e .

log_success "Base installation completed ✓"

# Ask about optional dependencies
echo
echo "Optional installations:"
echo "1) Development tools (recommended for contributors)"
echo "2) Rendering dependencies (for image generation)"
echo "3) All optional dependencies"
echo "4) Skip optional installations"
read -p "Choose installation option (1-4) [1]: " -n 1 -r
echo

case $REPLY in
    1|"")
        log_info "Installing development dependencies..."
        pip install -e ".[dev]"
        log_success "Development dependencies installed ✓"
        ;;
    2)
        log_info "Installing rendering dependencies..."
        pip install -e ".[rendering]"
        log_info "Installing Playwright browsers..."
        playwright install
        log_success "Rendering dependencies installed ✓"
        ;;
    3)
        log_info "Installing all optional dependencies..."
        pip install -e ".[dev,rendering]"
        log_info "Installing Playwright browsers..."
        playwright install
        log_success "All optional dependencies installed ✓"
        ;;
    4)
        log_info "Skipping optional installations"
        ;;
    *)
        log_warning "Invalid option, skipping optional installations"
        ;;
esac

# Verify installation
log_info "Verifying installation..."
if python -c "import vcd2image; print(f'$PROJECT_NAME {vcd2image.__version__} installed successfully')"; then
    log_success "Installation verification passed ✓"
else
    log_error "Installation verification failed"
    exit 1
fi

# Final instructions
echo
log_success "$PROJECT_NAME installation completed!"
echo
echo "Next steps:"
echo "1. Activate the virtual environment: source $VENV_DIR/bin/activate"
echo "2. Run tests: ./scripts/test.sh"
echo "3. Try the CLI: vcd2image --help"
echo "4. For image rendering, ensure you have the [rendering] dependencies installed"
echo
echo "For more information, see README.md"
