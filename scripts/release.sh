#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get current version from VERSION file
CURRENT_VERSION=$(cat VERSION)
echo -e "${BLUE}Current version:${NC} $CURRENT_VERSION"

# Calculate next version (increment patch)
MAJOR=$(echo $CURRENT_VERSION | cut -d. -f1)
MINOR=$(echo $CURRENT_VERSION | cut -d. -f2)
PATCH=$(echo $CURRENT_VERSION | cut -d. -f3)
NEXT_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"

# Get version from argument or suggest next version
if [ -n "$1" ]; then
    VERSION="$1"
else
    VERSION="$NEXT_VERSION"
fi
echo -e "${BLUE}Next version:${NC} $VERSION"

# Confirm with user
read -p "Continue with version $VERSION? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

# Update version in files
echo "$VERSION" > VERSION
sed -i.bak "s/version: \".*\"/version: \"$VERSION\"/" action.yml
rm action.yml.bak

# Show changes
echo -e "\n${BLUE}Changes to be committed:${NC}"
git diff VERSION action.yml

# Confirm changes
read -p "Commit these changes? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    git checkout VERSION action.yml
    echo "Changes reverted"
    exit 1
fi

# Commit and tag
git add VERSION action.yml
git commit -m "Release version $VERSION"
git tag -a "v$VERSION" -m "Release version $VERSION"

# Create major version tag
MAJOR_VERSION=$(echo $VERSION | cut -d. -f1)
git tag -fa "v$MAJOR_VERSION" -m "Update v$MAJOR_VERSION to $VERSION"

echo -e "\n${GREEN}✅ Ready to push! Run:${NC}"
echo "git push origin main v$VERSION v$MAJOR_VERSION -f" 