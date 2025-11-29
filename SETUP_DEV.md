# Development Setup

## Quick Syntax Check

Before running the game or committing code, you can quickly check for syntax errors:

```bash
./check_syntax.sh
```

This will catch indentation errors and other Python syntax issues before you try to run the game.

## Code Formatting (Optional)

### Using Black (Recommended)

Black is an opinionated Python code formatter that will automatically fix indentation and formatting issues.

**Install:**
```bash
pip install black
```

**Check formatting:**
```bash
black --check .
```

**Auto-format code:**
```bash
black .
```

### Using Ruff (Faster Alternative)

Ruff is a fast Python linter and formatter.

**Install:**
```bash
pip install ruff
```

**Check and fix:**
```bash
ruff check . --fix
ruff format .
```

## Pre-commit Hooks (Recommended)

Set up pre-commit hooks to automatically check code before committing:

```bash
pip install pre-commit
pre-commit install
```

This will automatically run syntax checks and formatting checks before each commit.

## IDE/Editor Settings

### VS Code / Cursor

Add to `.vscode/settings.json`:

```json
{
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true
  }
}
```

### PyCharm

1. Go to Settings → Tools → Actions on Save
2. Enable "Run Black"
3. Install Black plugin if needed

## Manual Syntax Check

You can also manually check a specific file:

```bash
python3 -m py_compile path/to/file.py
```

If there are no errors, this command will complete silently. If there are syntax errors, it will print them.

