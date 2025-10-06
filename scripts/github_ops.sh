#!/bin/bash
# VCD2Image GitHub Operations Script
# This script provides common GitHub operations for the project

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

# Check if git is available
if ! command -v git &> /dev/null; then
    log_error "Git is not installed or not in PATH"
    exit 1
fi

# Default repository URL
DEFAULT_REPO_URL="https://github.com/SJTU-YONGFU-RESEARCH-GRP/vcd2image.git"

# Get project info from pyproject.toml
PROJECT_NAME=$(grep '^name = ' pyproject.toml | sed 's/name = "\(.*\)"/\1/')
PROJECT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME="vcd2image"
fi

if [ -z "$PROJECT_VERSION" ]; then
    PROJECT_VERSION="0.1.0"
fi

# Function to check if we're in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository. Run 'git init' first."
        exit 1
    fi
}

# Function to check if remote exists
check_remote() {
    local remote_name=${1:-origin}
    if ! git remote get-url "$remote_name" > /dev/null 2>&1; then
        return 1
    fi
    return 0
}

# Function to get current branch
get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

# Function to check if working directory is clean
check_clean_working_dir() {
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "Working directory is not clean. Uncommitted changes detected."
        git status --short
        echo
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Initialize git repository
init_repo() {
    log_info "Initializing git repository..."

    if git rev-parse --git-dir > /dev/null 2>&1; then
        log_warning "Git repository already initialized"
        return 0
    fi

    git init
    log_success "Git repository initialized ✓"

    # Create .gitignore if it doesn't exist
    if [ ! -f ".gitignore" ]; then
        log_info "Creating .gitignore..."
        cat > .gitignore << 'EOF'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Output files
*.json
*.svg
*.png
*.pdf
*.html

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
EOF
        log_success ".gitignore created ✓"
    fi

    # Initial commit
    git add .
    git commit -m "Initial commit: $PROJECT_NAME v$PROJECT_VERSION"
    log_success "Initial commit created ✓"
}

# Set up remote repository
setup_remote() {
    local repo_url="$1"

    if [ -z "$repo_url" ]; then
        log_info "No repository URL provided, using default: $DEFAULT_REPO_URL"
        repo_url="$DEFAULT_REPO_URL"
    fi

    check_git_repo

    log_info "Setting up remote repository: $repo_url"

    if check_remote; then
        log_warning "Remote 'origin' already exists"
        git remote get-url origin
        read -p "Update remote URL? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git remote set-url origin "$repo_url"
            log_success "Remote URL updated ✓"
        fi
    else
        git remote add origin "$repo_url"
        log_success "Remote 'origin' added ✓"
    fi
}

# Push to remote repository
push_code() {
    local branch=${1:-$(get_current_branch)}
    local force=${2:-false}

    check_git_repo

    if ! check_remote; then
        log_error "No remote repository configured. Use 'remote' command first."
        exit 1
    fi

    check_clean_working_dir

    log_info "Pushing to remote repository (branch: $branch)..."

    if [ "$force" = true ]; then
        git push -u origin "$branch" --force-with-lease
    else
        git push -u origin "$branch"
    fi

    log_success "Code pushed to remote ✓"
}

# Create a new release
create_release() {
    local version="$1"
    local tag_message="$2"

    if [ -z "$version" ]; then
        log_error "Version is required for release"
        echo "Usage: $0 release <version> [tag-message]"
        exit 1
    fi

    check_git_repo

    if [ -z "$tag_message" ]; then
        tag_message="Release v$version"
    fi

    log_info "Creating release v$version..."

    # Check if tag already exists
    if git tag -l | grep -q "^v$version$"; then
        log_error "Tag v$version already exists"
        exit 1
    fi

    # Update version in pyproject.toml
    if [ -f "pyproject.toml" ]; then
        sed -i.bak "s/^version = \".*\"/version = \"$version\"/" pyproject.toml
        rm pyproject.toml.bak
        log_info "Updated version in pyproject.toml to $version"
    fi

    # Update version in __init__.py
    if [ -f "src/vcd2image/__init__.py" ]; then
        sed -i.bak "s/__version__ = \".*\"/__version__ = \"$version\"/" src/vcd2image/__init__.py
        rm src/vcd2image/__init__.py.bak
        log_info "Updated version in __init__.py to $version"
    fi

    # Commit version changes
    git add .
    git commit -m "Bump version to $version" || true

    # Create and push tag
    git tag -a "v$version" -m "$tag_message"
    git push origin "v$version"

    log_success "Release v$version created and pushed ✓"
}

# Create pull request branch
create_pr_branch() {
    local branch_name="$1"
    local base_branch=${2:-main}

    if [ -z "$branch_name" ]; then
        log_error "Branch name is required"
        echo "Usage: $0 pr-branch <branch-name> [base-branch]"
        exit 1
    fi

    check_git_repo

    log_info "Creating PR branch: $branch_name (base: $base_branch)"

    # Check if branch already exists
    if git show-ref --verify --quiet "refs/heads/$branch_name"; then
        log_error "Branch '$branch_name' already exists"
        exit 1
    fi

    # Create and switch to new branch
    git checkout -b "$branch_name" "$base_branch"
    log_success "Created and switched to branch '$branch_name' ✓"
}

# Show repository status
show_status() {
    check_git_repo

    echo "========================================"
    echo "📊 Repository Status"
    echo "========================================"

    echo "Project: $PROJECT_NAME v$PROJECT_VERSION"
    echo "Branch: $(get_current_branch)"
    echo

    if check_remote; then
        echo "Remote: $(git remote get-url origin)"
    else
        echo "Remote: Not configured"
    fi
    echo

    echo "Working directory status:"
    git status --short
    echo

    echo "Recent commits:"
    git log --oneline -5
    echo

    # Show submodule status if any exist
    if [ -f ".gitmodules" ]; then
        echo "Submodules:"
        git submodule status
        echo
    fi
}

# Git submodule operations
handle_submodule() {
    local sub_command="$1"
    shift

    check_git_repo

    case "$sub_command" in
        add)
            local repo_url="$1"
            local path="$2"

            if [ -z "$repo_url" ] || [ -z "$path" ]; then
                log_error "Repository URL and path are required"
                echo "Usage: $0 submodule add <url> <path>"
                exit 1
            fi

            log_info "Adding submodule: $repo_url -> $path"
            git submodule add "$repo_url" "$path"
            log_success "Submodule added ✓"

            # Update .gitmodules with proper formatting
            if [ -f ".gitmodules" ]; then
                log_info "Updating .gitmodules formatting..."
                # Ensure proper spacing and formatting
                sed -i 's/^\s*/\t/g' .gitmodules
            fi
            ;;

        update)
            log_info "Updating all submodules..."
            git submodule update --init --recursive
            log_success "Submodules updated ✓"
            ;;

        init)
            log_info "Initializing submodules..."
            git submodule init
            git submodule update
            log_success "Submodules initialized ✓"
            ;;

        status)
            log_info "Submodule status:"
            git submodule status
            ;;

        sync)
            log_info "Syncing submodule URLs..."
            git submodule sync --recursive
            log_success "Submodule URLs synced ✓"
            ;;

        foreach)
            local cmd="$*"
            if [ -z "$cmd" ]; then
                log_error "Command is required for foreach"
                echo "Usage: $0 submodule foreach <command>"
                exit 1
            fi

            log_info "Running command on all submodules: $cmd"
            git submodule foreach "$cmd"
            log_success "Command executed on all submodules ✓"
            ;;

        "")
            log_error "Submodule sub-command is required"
            echo "Available sub-commands: add, update, init, status, sync, foreach"
            exit 1
            ;;

        *)
            log_error "Unknown submodule sub-command: $sub_command"
            echo "Available sub-commands: add, update, init, status, sync, foreach"
            exit 1
            ;;
    esac
}

# Main command handling
case "${1:-help}" in
    init)
        init_repo
        ;;
    remote)
        setup_remote "$2"
        ;;
    push)
        push_code "$2" "$3"
        ;;
    release)
        create_release "$2" "$3"
        ;;
    pr-branch)
        create_pr_branch "$2" "$3"
        ;;
    status)
        show_status
        ;;
    submodule)
        handle_submodule "$2" "$3" "$4" "$5"
        ;;
    help|--help|-h)
        echo "VCD2Image GitHub Operations Script"
        echo
        echo "Usage: $0 <command> [arguments...]"
        echo
        echo "Commands:"
        echo "  init                    Initialize git repository"
        echo "  remote [url]           Set up remote repository (uses default if no URL)"
        echo "  push [branch] [force]  Push code to remote"
        echo "  release <version> [msg] Create and push a new release"
        echo "  pr-branch <name> [base] Create a new PR branch"
        echo "  status                 Show repository status"
        echo "  submodule <sub-cmd>    Git submodule operations"
        echo "  help                   Show this help message"
        echo
        echo "Submodule Commands:"
        echo "  submodule add <url> <path>  Add a new submodule"
        echo "  submodule update           Update all submodules"
        echo "  submodule init             Initialize submodules"
        echo "  submodule status           Show submodule status"
        echo "  submodule sync             Sync submodule URLs"
        echo
        echo "Examples:"
        echo "  $0 init"
        echo "  $0 remote"
        echo "  $0 remote https://github.com/your-org/your-repo.git"
        echo "  $0 push"
        echo "  $0 push main force"
        echo "  $0 release 1.0.0 \"First stable release\""
        echo "  $0 pr-branch feature/new-feature"
        echo "  $0 submodule add https://github.com/user/repo.git libs/repo"
        echo "  $0 submodule update"
        echo "  $0 submodule status"
        echo "  $0 status"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
