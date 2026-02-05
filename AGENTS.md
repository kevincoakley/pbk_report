# AGENTS.md

> Purpose: This file provides context, conventions, and setup instructions for AI agents working on this repository.

## 1. Project Overview
- Description: This project converts CSV files into a HTML report using Jinja2 templates.
- Language: Python
- Package Manager: `uv` (Do not use pip or poetry directly)

## 2. Directory Structure

```
.
├── AGENTS.md                           # This file
├── colleges.csv                        # CSV file containing college codes and names
├── country_codes.csv                   # CSV file containing country codes and names
├── coursecrit.csv                      # CSV file containing class to class type mappings
├── pbk_screening_apclasses.csv         # CSV file containing AP classes
├── pbk_screening_classes.csv           # CSV file containing regular classes
├── pbk_screening_ibclasses.csv         # CSV file containing IB classes
├── pbk_screening_transferclasses.csv   # CSV file containing transfer classes
├── pbk_screening.csv                   # CSV file containing student data
├── pbk_styling.j2                      # Jinja2 template for HTML report
├── pbk_styling.py                      # Main script
├── pbk_styling.py.html                 # Example correct HTML report
├── pyproject.toml                      # Project configuration
├── README.md                           # Project description
├── test_pbk_styling.py                 # Tests for the script
└── uv.lock                             # Lock file for dependencies
```

## 3. Development Workflow & Commands
Always use `uv` for package management and script execution.

### Setup
- First time setup: `uv sync` (Installs environment based on lockfile)
- Update environment: `uv sync`

### Dependency Management
- Add production dependency: `uv add <package_name>`
- Add dev/test dependency: `uv add <package_name> --group test`
- Remove dependency: `uv remove <package_name>`

### Running Code
- Run the styling script: `uv run python pbk_styling.py`
- Run arbitrary scripts: `uv run python <script_path>`

### Testing
- Run all tests: `uv run pytest`
- Write tests for new features
- Maintain existing test coverage
- Use pytest fixtures for common setup
- Name test files as `test_<module>.py`

## Development Workflow
1. Write/update tests first (TDD approach)
2. Implement changes
3. Run tests to ensure they pass
4. Format code with Black

## 4. Coding Conventions & Style

### Formatting
- Formatter: Black
  - Command: `uv run black .`
  - Rule: Always run formatting before declaring a task complete.
- Follow PEP 8 conventions
- Use type hints where appropriate
- Write docstrings for functions and classes

### Type Hinting
- Use standard Python type hints for function arguments and return values.
- Example: `def my_func(name: str) -> int:`

## 5. Critical Rules for Agents
- Do not update `uv.lock` manually. Use `uv add` or `uv sync`.
- Check `pyproject.toml` to see existing dependencies before adding new ones.
- Run tests after every significant code change to ensure no regressions.
- Ensure code is formatted with Black
- Preserve existing code style and patterns
- Ask for clarification if requirements are unclear