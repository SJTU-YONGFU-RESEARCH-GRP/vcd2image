#!/bin/bash
# VCD2Image Testing Script
# This script runs all tests and code quality checks

# Note: Removed 'set -e' to allow all tests to run even if some fail
# This way we can see all issues and fix them at once

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

# Global variable to track overall test success
OVERALL_SUCCESS=true
FAST_MODE=false

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
        OVERALL_SUCCESS=false
        return 0  # Don't exit, continue with other tests
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
        --fast)
            RUN_ALL=false
            RUN_UNIT=true
            FAST_MODE=true
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
            echo "  --unit     Run only unit tests (with coverage if available)"
            echo "  --fast     Run unit tests quickly (no coverage, stop on first failure)"
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
        # Check if required pytest plugins are available
        missing_plugins=""
        if ! python3 -c "import pytest_mock" 2>/dev/null; then
            missing_plugins="$missing_plugins pytest-mock"
        fi
        if ! python3 -c "import pytest_asyncio" 2>/dev/null; then
            missing_plugins="$missing_plugins pytest-asyncio"
        fi

        if [ -n "$missing_plugins" ]; then
            log_warning "Missing required pytest plugins:$missing_plugins"
            log_info "Install with: pip install$missing_plugins"
            log_error "Cannot run tests without required plugins"
            OVERALL_SUCCESS=false
            return 0
        else
            if [ "$FAST_MODE" = true ]; then
                # Check if pytest-xdist is available for parallel execution
                if python3 -c "import xdist" 2>/dev/null; then
                    run_with_timing "pytest -x --tb=line -n auto" "Fast parallel unit tests"
                else
                    run_with_timing "pytest -x --tb=line" "Fast unit tests (no coverage, stop on failure)"
                fi
            else
                # Check if pytest-cov is available
                if python3 -c "import pytest_cov" 2>/dev/null; then
                    run_with_timing "pytest --cov=vcd2image --cov-report=term-missing --cov-report=html" "Unit tests with coverage"
                else
                    run_with_timing "pytest" "Unit tests (coverage not available)"
                fi
            fi
        fi
    else
        log_warning "pytest not found, skipping unit tests"
        log_info "Install with: pip install pytest pytest-cov pytest-asyncio pytest-mock"
    fi
fi

# Run vcd2image examples
if [ "$RUN_ALL" = true ] || [ "$RUN_EXAMPLES" = true ]; then
    if command -v python &> /dev/null; then
        # Change to examples directory for default file paths
        cd examples

        # Define test output files with unique names
        TEST_JSON="test_timer.json"
        TEST_PNG="test_timer.png"
        TEST_FULL_PNG="test_timer_full.png"
        TEST_AUTO_PNG="test_timer_auto.png"
        TEST_FIGURES_DIR="test_figures"

        # Clean up any existing test files from previous runs
        log_info "Cleaning up previous test outputs..."
        rm -f "$TEST_JSON" "$TEST_PNG" "$TEST_FULL_PNG" "$TEST_AUTO_PNG"
        rm -rf "$TEST_FIGURES_DIR"

        # Extract signals from VCD to JSON (using test-specific output name)
        run_with_timing "python -m vcd2image.cli.main timer.vcd -o $TEST_JSON -s tb_timer/u_timer/clock tb_timer/u_timer/reset tb_timer/u_timer/pulse tb_timer/u_timer/count_eq11 tb_timer/u_timer/count" "VCD to JSON conversion"

        # Convert JSON to PNG image
        run_with_timing "python -m vcd2image.cli.main $TEST_JSON -i $TEST_PNG" "JSON to PNG conversion"

        # Run the full pipeline example (VCD -> JSON -> PNG in one command)
        run_with_timing "python -m vcd2image.cli.main timer.vcd -s tb_timer/u_timer/clock tb_timer/u_timer/reset tb_timer/u_timer/pulse tb_timer/u_timer/count_eq11 tb_timer/u_timer/count --image $TEST_FULL_PNG" "Full pipeline conversion"

        # Auto plotting: Single organized plot
        run_with_timing "python -m vcd2image.cli.main timer.vcd --auto-plot --image $TEST_AUTO_PNG" "Auto plotting (single figure)"

        # Auto plotting: Multiple categorized figures
        mkdir -p "$TEST_FIGURES_DIR"
        run_with_timing "python -m vcd2image.cli.main timer.vcd --auto-plot --plot-dir $TEST_FIGURES_DIR --plot-formats png svg" "Auto plotting (multiple figures)"

        # List available signals
        log_info "Listing available signals in timer.vcd..."
        python -m vcd2image.cli.main timer.vcd --list-signals

        # Verify all outputs are in examples directory
        log_info "Verifying all generated files are in examples/ directory..."
        GENERATED_FILES="$TEST_JSON $TEST_PNG $TEST_FULL_PNG $TEST_AUTO_PNG"
        MISSING_FILES=""

        for file in $GENERATED_FILES; do
            if [ -f "$file" ]; then
                log_success "✓ Generated file found: $file"
            else
                log_error "✗ Generated file missing: $file"
                MISSING_FILES="$MISSING_FILES $file"
            fi
        done

        if [ -d "$TEST_FIGURES_DIR" ]; then
            FIGURE_COUNT=$(find "$TEST_FIGURES_DIR" -type f | wc -l)
            log_success "✓ Generated figures directory with $FIGURE_COUNT files: $TEST_FIGURES_DIR/"
        else
            log_error "✗ Generated figures directory missing: $TEST_FIGURES_DIR/"
            MISSING_FILES="$MISSING_FILES $TEST_FIGURES_DIR/"
        fi

        # Check for file name conflicts with existing files
        EXISTING_FILES="timer.json timer_lazy.json example.py timer.v timer.vcd"
        CONFLICTS_FOUND=""

        for gen_file in $GENERATED_FILES; do
            for existing in $EXISTING_FILES; do
                if [ "$gen_file" = "$existing" ]; then
                    log_warning "⚠ File name conflict detected: $gen_file (using test-specific names to avoid conflicts)"
                    CONFLICTS_FOUND="$CONFLICTS_FOUND $gen_file"
                fi
            done
        done

        if [ -n "$CONFLICTS_FOUND" ]; then
            log_info "Note: Test files use unique names to avoid overwriting existing files"
        fi

        # Clean up test files
        log_info "Cleaning up test output files..."
        rm -f $GENERATED_FILES
        rm -rf "$TEST_FIGURES_DIR"

        # Report results
        if [ -z "$MISSING_FILES" ]; then
            log_success "All example tests passed with proper file isolation!"
        else
            log_error "Some files were not generated properly: $MISSING_FILES"
            exit 1
        fi

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
if [ "$OVERALL_SUCCESS" = true ]; then
    log_success "All requested tests completed successfully!"
    echo "========================================"
    exit 0
else
    log_error "Some tests failed. Please review the output above and fix the issues."
    echo "========================================"
    exit 1
fi
