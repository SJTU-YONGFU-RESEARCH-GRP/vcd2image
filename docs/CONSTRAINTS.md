# Python and README Implementation Constraints

## Critical Rules - NO EXCEPTIONS

### Complete Implementation Requirements
- **NEVER generate incomplete code** - Always provide fully functional, runnable implementations
- **Complete all functions** - Every function must have complete body with proper return statements
- **Finish all classes** - Include all methods and properties that are referenced
- **No TODO comments** - Complete all functionality instead of leaving placeholders
- **No placeholder returns** - Functions must return actual values, not `None` or `...`

### Accuracy Requirements
- **Use only existing APIs** - Never invent or assume library methods/functions that don't exist
- **Verify all imports** - Ensure all imports resolve to actual modules/packages
- **Validate file paths** - Only reference files that actually exist in the project
- **Check method signatures** - Verify all function calls use correct parameters
- **Verify syntax** - All code must be syntactically correct and executable

### Code Quality Standards
- **Python Version:** 3.10+
- **Type Annotations:** All functions, methods, and class members must have type annotations
- **Documentation:** Google-style docstrings for all functions and classes
- **Error Handling:** Use specific exception types with informative messages
- **Testing:** Comprehensive unit tests using pytest only

### Code Organization & Management
- **File Size Limit:** Keep each file under 1000 lines of code
- **Single Responsibility:** One class per file (except for small utility classes)
- **Modular Design:** Separate concerns into different modules/packages
- **CLI Interface:** Implement command-line interface using `argparse` or `click`
- **Logging:** Use Python's `logging` module for all operations (info, warning, error levels)
- **Configuration:** Use environment variables or config files, never hardcode values
- **Dependency Management:** Use `requirements.txt` or `pyproject.toml` for dependencies

### Recommended Libraries & Tools
- **CLI:** `argparse` (built-in) or `click` for advanced CLI features
- **Logging:** `logging` (built-in) with proper configuration
- **Data Processing:** `pandas`, `numpy` for data manipulation
- **Configuration:** `python-dotenv` for environment variables, `pydantic` for validation
- **Testing:** `pytest`, `pytest-cov` for coverage
- **Code Quality:** `ruff` for linting/formatting, `mypy` for type checking
- **File Operations:** `pathlib` for path handling, `shutil` for file operations
- **Async Operations:** `asyncio`, `aiofiles` for async I/O
- **Progress Bars:** `tqdm` for long-running operations
- **JSON/YAML:** `json` (built-in), `pyyaml` for configuration files

### Project Structure Requirements
```
project/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── core/                # Core business logic
│   ├── utils/               # Utility functions
│   ├── config/              # Configuration management
│   └── models/              # Data models/classes
├── tests/
│   ├── __init__.py
│   ├── test_core/
│   └── test_utils/
├── requirements.txt
├── pyproject.toml
└── README.md
```

### What NOT to Include
- No fake/mock data or placeholder values
- No hardcoded values or configuration
- No unused imports, functions, or variables
- No redundant code or duplicate logic
- No incomplete implementations

### Verification Checklist
Before delivering code, verify:
- [ ] All imports resolve without errors
- [ ] All functions have complete implementations
- [ ] All classes include all referenced methods
- [ ] All file paths reference existing files
- [ ] All code is syntactically correct
- [ ] All examples can be run immediately
- [ ] All error handling is complete
- [ ] Each file is under 1000 lines of code
- [ ] One class per file (except small utilities)
- [ ] CLI interface is implemented and functional
- [ ] Logging is properly configured and used
- [ ] Dependencies are listed in requirements.txt or pyproject.toml

**Remember: Study PLAN.md and testcases/ before implementation. Generate only complete, working Python code.**