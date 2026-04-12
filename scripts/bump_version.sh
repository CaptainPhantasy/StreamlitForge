#!/bin/bash
# Bump version across the project

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/bump_version.sh <version>"
    echo "Example: ./scripts/bump_version.sh 0.2.0"
    exit 1
fi

VERSION=$1
echo "Bumping version to $VERSION"

# Update pyproject.toml
sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update CLI version
sed -i.bak "s/version_option(version=\".*\")/version_option(version=\"$VERSION\")/" streamlitforge/cli.py
rm streamlitforge/cli.py.bak

# Update __init__.py
echo "__version__ = \"$VERSION\"" > streamlitforge/__init__.py

# Update requirements.txt
sed -i.bak "s/streamlit==.*/streamlit==$VERSION/" requirements.txt
rm requirements.txt.bak

echo "Version bumped to $VERSION"
echo ""
echo "Changes made:"
echo "  - pyproject.toml version"
echo "  - streamlitforge/__init__.py"
echo "  - streamlitforge/cli.py"
echo "  - requirements.txt"
echo ""
echo "Commit with: git commit -am \"chore: Bump version to $VERSION\""
echo "Then push: git push origin main"
echo ""
echo "Tag with: git tag -a v$VERSION -m \"Release $VERSION\""
echo "Then push: git push origin v$VERSION"
