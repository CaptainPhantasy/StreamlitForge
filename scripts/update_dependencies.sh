#!/bin/bash
# Update dependencies and create lock file

set -e

echo "=== Updating Dependencies ==="

# Update pip
pip install --upgrade pip

# Install current requirements
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Generate lock file
pip freeze > requirements-lock.txt

# Verify
echo ""
echo "=== Verification ==="
echo "Total packages: $(wc -l < requirements-lock.txt)"
echo "Version ranges: $(grep -c -E '>|<|~=' requirements-lock.txt || echo 0)"

if [ $(grep -c -E '>|<|~=' requirements-lock.txt || echo 0) -eq 0 ]; then
    echo ""
    echo -e "✓ All versions pinned!"
    echo "Review requirements-lock.txt and commit if correct"
else
    echo ""
    echo -e "⚠ WARNING: Version ranges found in lock file"
    echo "Review and update to exact versions"
fi

echo ""
echo "=== Done ==="
