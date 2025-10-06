#!/bin/bash
# VCD2Image Testing Script
# This script runs all tests and code quality checks

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

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    log_info "Virtual environment detected: $VIRTUAL_ENV"
else
    log_warning "No virtual environment detected. Consider running: source venv/bin/activate"
fi

# Function to run a command with timing
run_with_timing() {
    local cmd="$1"
    local desc="$2"
    log_info "Running $desc..."
    local start_time=$(date +%s)

    if eval "$cmd"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        log_success "$desc completed in ${duration}s ✓"
        return 0
    else
        log_error "$desc failed"
        return 1
    fi
}

# Parse command line arguments
RUN_ALL=true
RUN_UNIT=false
RUN_LINT=false
RUN_TYPE=false
RUN_FORMAT=false
RUN_EXAMPLES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_ALL=false
            RUN_UNIT=true
            shift
            ;;
        --lint)
            RUN_ALL=false
            RUN_LINT=true
            shift
            ;;
        --type)
            RUN_ALL=false
            RUN_TYPE=true
            shift
            ;;
        --format)
            RUN_ALL=false
            RUN_FORMAT=true
            shift
            ;;
        --examples)
            RUN_ALL=false
            RUN_EXAMPLES=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit     Run only unit tests"
            echo "  --lint     Run only linting checks"
            echo "  --type     Run only type checking"
            echo "  --format   Run only code formatting"
            echo "  --examples Run only vcd2image examples"
            echo "  --help     Show this help message"
            echo ""
            echo "If no options are provided, all checks are run."
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "========================================"
echo "🧪 VCD2Image Testing Suite"
echo "========================================"

# Run code formatting check
if [ "$RUN_ALL" = true ] || [ "$RUN_FORMAT" = true ]; then
    if command -v ruff &> /dev/null; then
        run_with_timing "ruff format --check --diff ." "Code formatting check"
    else
        log_warning "ruff not found, skipping code formatting check"
    fi
fi

# Run linting
if [ "$RUN_ALL" = true ] || [ "$RUN_LINT" = true ]; then
    if command -v ruff &> /dev/null; then
        run_with_timing "ruff check ." "Code linting"
    else
        log_warning "ruff not found, skipping linting"
        log_info "Install with: pip install ruff"
    fi
fi

# Run type checking
if [ "$RUN_ALL" = true ] || [ "$RUN_TYPE" = true ]; then
    if command -v mypy &> /dev/null; then
        run_with_timing "mypy src/" "Type checking"
    else
        log_warning "mypy not found, skipping type checking"
        log_info "Install with: pip install mypy"
    fi
fi

# Run unit tests
if [ "$RUN_ALL" = true ] || [ "$RUN_UNIT" = true ]; then
    if command -v pytest &> /dev/null; then
        run_with_timing "pytest --cov=vcd2image --cov-report=term-missing --cov-report=html" "Unit tests with coverage"
    else
        log_warning "pytest not found, skipping unit tests"
        log_info "Install with: pip install pytest pytest-cov"
    fi
fi

# Run vcd2image examples
if [ "$RUN_ALL" = true ] || [ "$RUN_EXAMPLES" = true ]; then
    if command -v python &> /dev/null; then
        # Change to examples directory for default file paths
        cd examples

        # Extract signals from VCD to JSON
        run_with_timing "python -m vcd2image.cli.main timer.vcd -o timer.json -s tb_timer/u_timer/clock tb_timer/u_timer/reset tb_timer/u_timer/pulse tb_timer/u_timer/count_eq11 tb_timer/u_timer/count" "VCD to JSON conversion"

        # Convert JSON to PNG image
        run_with_timing "python -m vcd2image.cli.main timer.json -i timer.png" "JSON to PNG conversion"

        # Run the full pipeline example (VCD -> JSON -> PNG in one command)
        run_with_timing "python -m vcd2image.cli.main timer.vcd -s tb_timer/u_timer/clock tb_timer/u_timer/reset tb_timer/u_timer/pulse tb_timer/u_timer/count_eq11 tb_timer/u_timer/count --image timer_full.png" "Full pipeline conversion"

        # List available signals
        log_info "Listing available signals in timer.vcd..."
        python -m vcd2image.cli.main timer.vcd --list-signals

        # Go back to project root
        cd ..
    else
        log_warning "python not found, skipping examples"
    fi
fi

# Generate coverage report
if [ "$RUN_ALL" = true ] || [ "$RUN_UNIT" = true ]; then
    if [ -d "htmlcov" ]; then
        log_info "Coverage report generated: htmlcov/index.html"
    fi
fi

echo
echo "========================================"
log_success "All requested tests completed!"
echo "========================================"

# Exit with success
exit 0
