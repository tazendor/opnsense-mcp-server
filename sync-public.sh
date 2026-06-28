#!/usr/bin/env bash
# Merge main into the public branch (strips .specify/) and push to the public remote.
set -euo pipefail

CURRENT=$(git rev-parse --abbrev-ref HEAD)

echo "Switching to public branch..."
git checkout public

echo "Merging main..."
git merge main --no-edit

# .specify/ may have been re-introduced by the merge; re-strip it.
if git ls-files --error-unmatch .specify/ &>/dev/null 2>&1; then
    echo "Re-stripping .specify/ after merge..."
    git rm --cached -r .specify/
    git commit -m "Remove .specify/ from public branch"
fi

echo "Pushing to public remote..."
git push public public:main

echo "Returning to $CURRENT..."
git checkout "$CURRENT"

echo "Done. Public repo is up to date."
