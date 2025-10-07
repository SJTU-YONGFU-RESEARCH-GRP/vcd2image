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

### `setup-testing.sh`
**Purpose**: Quick setup script for testing environment and tool verification.

**Features**:
- Creates virtual environment if it doesn't exist
- Activates virtual environment
- Installs all development and rendering dependencies
- Verifies tool installations (pytest, ruff, mypy)
- Runs basic import verification tests
- Provides next steps and usage instructions

**Usage**:
```bash
./scripts/setup-testing.sh
```

**What it does**:
1. Checks Python version compatibility
2. Creates virtual environment (`venv/`)
3. Activates virtual environment
4. Upgrades pip
5. Installs package with `[dev,rendering]` extras
6. Verifies tool availability
7. Runs basic import verification
8. Displays next steps

**Platform notes**:
- Designed for Unix-like systems (Linux, macOS)
- On Windows, run with: `bash scripts/setup-testing.sh`
- Requires Python 3.10+ in PATH as `python3`

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

### `clean.sh`
**Purpose**: Clean generated files and build artifacts from the project.

**Features**:
- Clean examples directory (remove generated JSON, PNG, HTML, SVG files)
- Clean build artifacts and caches
- Dry-run mode to preview what will be deleted
- Interactive confirmation (with force option)
- Colored output for better readability

**Usage**:
```bash
# Clean examples directory (default)
./scripts/clean.sh

# Same as above (explicit target)
./scripts/clean.sh examples

# Clean everything (examples + build artifacts, caches)
./scripts/clean.sh all

# Preview what would be deleted (dry run)
./scripts/clean.sh --dry-run
./scripts/clean.sh examples --dry-run
./scripts/clean.sh all --dry-run

# Skip confirmation prompts
./scripts/clean.sh --force
./scripts/clean.sh examples --force
./scripts/clean.sh all --force

# Show help
./scripts/clean.sh --help
```

**What gets cleaned**:

**Examples directory** (`./scripts/clean.sh examples`):
- All JSON files (*.json) - WaveJSON data files
- All PNG files (*.png) - Generated images
- All HTML files (*.html) - Interactive waveforms
- All SVG files (*.svg) - Vector graphics
- Generated directories (*single_figure/, *categorized_figures/, *wave_skins/, *multi_format/, *signal_grouping/, *cli_equivalents/, *batch_processing/, figures/)

**Keeps**: timer.v, timer.vcd, example.py, README.md

**Directory removal pattern**: Removes any directory ending with:
- `*single_figure` (from example 4)
- `*categorized_figures` (from example 5)
- `*wave_skins` (from example 6)
- `*multi_format` (from example 8)
- `*signal_grouping` (from example 10)
- `*cli_equivalents` (from example 11)
- `*batch_processing` (from example 13)
- `figures` (legacy from example 5)

**Full clean** (`./scripts/clean.sh all`):
- Everything in examples directory
- Python cache files (__pycache__/, *.pyc)
- Build artifacts (build/, dist/, *.egg-info/)
- Coverage reports (htmlcov/, .coverage)
- Linter caches (.ruff_cache/, .mypy_cache/)

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

### For `clean.sh`:
- Bash shell (Unix-like systems or Git Bash on Windows)
- Basic Unix utilities (find, rm)
- On Windows, use Git Bash or WSL to run the script

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

# 7. Clean generated files before committing (optional)
./scripts/clean.sh examples

# 8. Push changes
./scripts/github_ops.sh push

# 9. Create releases as needed
./scripts/github_ops.sh release 0.1.0 "Initial release"
```

**Cleaning workflow**:

```bash
# Clean examples directory after running examples
./scripts/clean.sh examples

# Clean everything (examples + build artifacts) for fresh start
./scripts/clean.sh all

# Preview what would be cleaned
./scripts/clean.sh --dry-run
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
