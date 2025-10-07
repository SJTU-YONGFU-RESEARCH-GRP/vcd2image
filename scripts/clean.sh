#!/bin/bash

# Clean script for VCD2Image
# Removes generated files from examples directory, keeping only input files

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Examples directory
EXAMPLES_DIR="$PROJECT_ROOT/examples"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to show usage
show_usage() {
    echo "VCD2Image Clean Script"
    echo ""
    echo "Usage: $0 [OPTIONS] [TARGET]"
    echo ""
    echo "Targets:"
    echo "  examples    Clean examples directory (default)"
    echo "  all         Clean examples and other generated files"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -n, --dry-run  Show what would be deleted without actually deleting"
    echo "  -f, --force    Skip confirmation prompts"
    echo ""
    echo "Examples:"
    echo "  $0              # Clean examples directory"
    echo "  $0 examples     # Same as above"
    echo "  $0 --dry-run    # Show what would be cleaned"
    echo "  $0 all          # Clean everything"
}

# Function to confirm action
confirm() {
    local message="$1"
    if [[ "$FORCE" == "true" ]]; then
        return 0
    fi

    echo -e "${YELLOW}$message${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# Function to clean examples directory
clean_examples() {
    print_info "Cleaning examples directory..."

    if [[ ! -d "$EXAMPLES_DIR" ]]; then
        print_error "Examples directory not found: $EXAMPLES_DIR"
        return 1
    fi

    cd "$EXAMPLES_DIR"

    # Files to keep (input files and scripts)
    local keep_files=("timer.v" "timer.vcd" "example.py" "README.md")
    local keep_dirs=()

    # Collect files to remove
    local files_to_remove=()
    local dirs_to_remove=()

    # Find all JSON, PNG, HTML files
    while IFS= read -r -d '' file; do
        # Check if file should be kept
        local keep_file=false
        for keep in "${keep_files[@]}"; do
            if [[ "$(basename "$file")" == "$keep" ]]; then
                keep_file=true
                break
            fi
        done

        if [[ "$keep_file" == "false" ]]; then
            files_to_remove+=("$file")
        fi
    done < <(find . -maxdepth 1 -type f \( -name "*.json" -o -name "*.png" -o -name "*.html" -o -name "*.svg" \) -print0 2>/dev/null)

    # Find directories to remove (generated output directories)
    while IFS= read -r -d '' dir; do
        local dirname=$(basename "$dir")
        case "$dirname" in
            *signal_grouping|*cli_equivalents|*batch_processing|*categorized_figures|*wave_skins|*multi_format|*single_figure|figures|[0-9]*_*)
                dirs_to_remove+=("$dir")
                ;;
        esac
    done < <(find . -maxdepth 1 -type d -not -name "." -not -name ".." -print0 2>/dev/null)

    # Show what will be removed
    if [[ ${#files_to_remove[@]} -gt 0 || ${#dirs_to_remove[@]} -gt 0 ]]; then
        echo "Files to be removed:"
        for file in "${files_to_remove[@]}"; do
            echo "  $(basename "$file")"
        done

        echo "Directories to be removed:"
        for dir in "${dirs_to_remove[@]}"; do
            echo "  $(basename "$dir")/"
        done

        if [[ "$DRY_RUN" != "true" ]]; then
            if confirm "This will permanently delete the above files and directories."; then
                # Remove files
                for file in "${files_to_remove[@]}"; do
                    rm -f "$file"
                    print_success "Removed: $(basename "$file")"
                done

                # Remove directories
                for dir in "${dirs_to_remove[@]}"; do
                    rm -rf "$dir"
                    print_success "Removed directory: $(basename "$dir")/"
                done
            else
                print_info "Operation cancelled."
                return 0
            fi
        else
            print_info "Dry run - no files removed."
        fi
    else
        print_success "Examples directory is already clean!"
    fi
}

# Function to clean everything
clean_all() {
    print_warning "Cleaning all generated files (including build artifacts, caches, etc.)"

    if [[ "$DRY_RUN" != "true" ]]; then
        if ! confirm "This will clean examples AND remove build artifacts, caches, and other generated files."; then
            print_info "Operation cancelled."
            return 0
        fi
    fi

    # Clean examples first
    clean_examples

    # Clean other generated files
    cd "$PROJECT_ROOT"

    # Python cache files
    print_info "Removing Python cache files..."
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

    # Build artifacts
    if [[ -d "build" ]]; then
        rm -rf build
        print_success "Removed: build/"
    fi

    if [[ -d "dist" ]]; then
        rm -rf dist
        print_success "Removed: dist/"
    fi

    # Coverage reports
    if [[ -d "htmlcov" ]]; then
        rm -rf htmlcov
        print_success "Removed: htmlcov/"
    fi

    if [[ -f ".coverage" ]]; then
        rm -f .coverage
        print_success "Removed: .coverage"
    fi

    # Ruff cache
    if [[ -d ".ruff_cache" ]]; then
        rm -rf .ruff_cache
        print_success "Removed: .ruff_cache/"
    fi

    # MyPy cache
    if [[ -d ".mypy_cache" ]]; then
        rm -rf .mypy_cache
        print_success "Removed: .mypy_cache/"
    fi

    print_success "Full cleanup completed!"
}

# Parse command line arguments
DRY_RUN=false
FORCE=false
TARGET="examples"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        examples|all)
            TARGET="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
print_info "VCD2Image Clean Script"
echo "Target: $TARGET"
if [[ "$DRY_RUN" == "true" ]]; then
    echo "Mode: Dry run (no files will be deleted)"
fi
echo

case "$TARGET" in
    examples)
        clean_examples
        ;;
    all)
        clean_all
        ;;
    *)
        print_error "Invalid target: $TARGET"
        show_usage
        exit 1
        ;;
esac

print_success "Clean operation completed!"
