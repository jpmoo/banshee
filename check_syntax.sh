#!/bin/bash
# Quick syntax check for Python files
# Run this before committing to catch indentation and syntax errors early

echo "Checking Python syntax..."

# Find all Python files (excluding venv)
find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*" | while read file; do
    echo "Checking $file..."
    python3 -m py_compile "$file" 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ Syntax error in $file"
        exit 1
    fi
done

if [ $? -eq 0 ]; then
    echo "✅ All Python files have valid syntax!"
    exit 0
else
    echo "❌ Syntax errors found. Please fix before committing."
    exit 1
fi

