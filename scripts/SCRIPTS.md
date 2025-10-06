# VCD2Image Scripts

This directory contains utility scripts to help with development, testing, and deployment of VCD2Image.

## 🚀 Scripts Overview

### `install.sh`
**Purpose**: Set up the development environment and install dependencies.

**Features**:
- Creates and activates virtual environment
- Installs the package in development mode
- Optionally installs development tools and rendering dependencies
- Verifies installation

**Usage**:
```bash
./scripts/install.sh
```

**Options**: Interactive menu for optional dependencies
- Development tools (pytest, ruff, mypy)
- Rendering dependencies (playwright, pillow)
- All optional dependencies

### `test.sh`
**Purpose**: Run comprehensive testing suite including code quality checks.

**Features**:
- Code formatting check (ruff format)
- Linting (ruff check)
- Type checking (mypy)
- Unit tests with coverage (pytest)
- Timing information for each step

**Usage**:
```bash
# Run all tests
./scripts/test.sh

# Run specific test types
./scripts/test.sh --unit     # Only unit tests
./scripts/test.sh --lint     # Only linting
./scripts/test.sh --type     # Only type checking
./scripts/test.sh --format   # Only formatting check
```

### `github_ops.sh`
**Purpose**: Handle common GitHub operations for repository management.

**Features**:
- Initialize git repository with proper .gitignore
- Set up remote repository (defaults to VCD2Image repo)
- Push code to remote
- Create releases with version bumping
- Create PR branches
- **Git submodule operations** (add, update, init, status, sync, foreach)
- Show repository status

**Usage**:
```bash
# Initialize repository
./scripts/github_ops.sh init

# Set up remote (uses default VCD2Image repo)
./scripts/github_ops.sh remote

# Or specify custom remote
./scripts/github_ops.sh remote https://github.com/your-org/your-repo.git

# Push current branch
./scripts/github_ops.sh push

# Force push (use with caution)
./scripts/github_ops.sh push main force

# Create a release
./scripts/github_ops.sh release 1.0.0 "First stable release"

# Create a PR branch
./scripts/github_ops.sh pr-branch feature/new-feature

# Submodule operations
./scripts/github_ops.sh submodule add https://github.com/user/repo.git libs/repo
./scripts/github_ops.sh submodule update
./scripts/github_ops.sh submodule status
./scripts/github_ops.sh submodule init
./scripts/github_ops.sh submodule sync
./scripts/github_ops.sh submodule foreach "git pull origin main"

# Show repository status
./scripts/github_ops.sh status

# Show help
./scripts/github_ops.sh help
```

## 🔧 Prerequisites

### For `install.sh`:
- Python 3.10+
- Internet connection for downloading dependencies

### For `test.sh`:
- Virtual environment activated
- Dependencies installed (run `install.sh` first)

### For `github_ops.sh`:
- Git installed and configured
- Repository initialized (use `init` command)

## 📋 Development Workflow

A typical development workflow using these scripts:

```bash
# 1. Initial setup
./scripts/install.sh

# 2. Activate virtual environment (if not done by install.sh)
source venv/bin/activate

# 3. Initialize git repo and set up remote
./scripts/github_ops.sh init
./scripts/github_ops.sh remote

# 4. Initialize and update submodules (if any)
./scripts/github_ops.sh submodule update

# 5. Make code changes...

# 6. Run tests
./scripts/test.sh

# 7. Push changes
./scripts/github_ops.sh push

# 8. Create releases as needed
./scripts/github_ops.sh release 0.1.0 "Initial release"
```

For projects with submodules:

```bash
# Add a new submodule
./scripts/github_ops.sh submodule add https://github.com/library/repo.git libs/repo

# Initialize submodules for new clones
./scripts/github_ops.sh submodule update

# Update all submodules to latest
./scripts/github_ops.sh submodule foreach "git pull origin main"
```

## 🔍 Troubleshooting

### Common Issues:

**"Permission denied" when running scripts**:
- On Unix-like systems, make sure scripts are executable: `chmod +x scripts/*.sh`
- On Windows, run with bash: `bash scripts/install.sh`

**Virtual environment not found**:
- Run `install.sh` first to create the virtual environment
- Activate with: `source venv/bin/activate`

**Git operations fail**:
- Ensure git is installed and configured
- Check that you're in the correct directory
- Verify remote repository URL is correct

**Submodule issues**:
- After cloning, run `./scripts/github_ops.sh submodule update`
- For existing repos, run `./scripts/github_ops.sh submodule init` first
- Use `./scripts/github_ops.sh submodule status` to check submodule state
- If submodules fail to update, try `./scripts/github_ops.sh submodule sync` first

**Tests fail due to missing dependencies**:
- Install development dependencies: `pip install -e ".[dev]"`
- For rendering tests: `pip install -e ".[rendering]"`

## 🎯 Best Practices

1. **Always run tests before pushing**: `./scripts/test.sh`
2. **Use meaningful commit messages**: The scripts will help with release commits
3. **Keep virtual environment activated**: Scripts check for this
4. **Regular releases**: Use the release command for version bumps
5. **Clean working directory**: Scripts warn about uncommitted changes

## 📝 Notes

- Scripts are designed to be idempotent (safe to run multiple times)
- All scripts provide colored output for better readability
- Error handling is built-in with clear error messages
- Scripts work on Unix-like systems (Linux, macOS) and Windows with WSL/Git Bash
