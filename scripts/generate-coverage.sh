#!/bin/bash
# VCD2Image Coverage Report Generator
# This script generates local coverage reports for development

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

log_info "Generating coverage reports for VCD2Image..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    log_info "Virtual environment detected: $VIRTUAL_ENV"
else
    log_warning "No virtual environment detected. Consider running: source venv/bin/activate"
fi

# Check if pytest-cov is available
if ! python -c "import pytest_cov" 2>/dev/null; then
    log_error "pytest-cov not found. Install with: pip install pytest-cov"
    exit 1
fi

# Clean up previous coverage reports
log_info "Cleaning up previous coverage reports..."
rm -rf htmlcov/
rm -f coverage.xml .coverage

# Run tests with coverage
log_info "Running tests with coverage..."
if pytest --cov=vcd2image --cov-report=term-missing --cov-report=xml --cov-report=html; then
    log_success "Coverage tests completed successfully"

    # Check if coverage files were generated
    if [ -f "coverage.xml" ]; then
        log_success "XML coverage report generated: coverage.xml"
    else
        log_warning "XML coverage report not found"
    fi

    if [ -d "htmlcov/" ]; then
        log_success "HTML coverage report generated: htmlcov/index.html"
        log_info "Open htmlcov/index.html in your browser to view detailed coverage"
    else
        log_warning "HTML coverage report not found"
    fi

    # Show coverage summary
    log_info "Coverage Summary:"
    if command -v coverage &> /dev/null; then
        coverage report --show-missing
    else
        log_warning "coverage command not available, install with: pip install coverage"
        log_info "Basic coverage info available in terminal output above"
    fi

    echo ""
    log_info "Coverage reports generated successfully!"
    echo ""
    log_info "Files created:"
    echo "  - htmlcov/index.html    (Interactive HTML report)"
    echo "  - coverage.xml          (XML format for CI/tools)"
    echo "  - .coverage             (Python coverage data)"
    echo ""
    log_info "To view HTML report:"
    echo "  python -m http.server 8000 -d htmlcov/"
    echo "  Then open http://localhost:8000 in your browser"

else
    log_error "Coverage tests failed"
    exit 1
fi
