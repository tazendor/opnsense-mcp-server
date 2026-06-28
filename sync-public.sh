#!/usr/bin/env bash
# Merge main into the public branch, strip internal artifacts, push to public remote.
set -euo pipefail

CURRENT=$(git rev-parse --abbrev-ref HEAD)

echo "Switching to public branch..."
git checkout public

echo "Merging main..."
git merge main --no-edit

# Strip internal artifacts re-introduced by the merge.
STRIP_PATHS=(.specify/ specs/ CLAUDE.md sync-public.sh)
STRIPPED=()
for path in "${STRIP_PATHS[@]}"; do
    if git ls-files --error-unmatch "$path" &>/dev/null 2>&1; then
        git rm --cached -r "$path"
        STRIPPED+=("$path")
    fi
done
if [ ${#STRIPPED[@]} -gt 0 ]; then
    echo "Re-stripping: ${STRIPPED[*]}"
    git commit -m "Remove internal artifacts from public branch"
fi

echo "Pushing to public remote..."
git push public public:main

echo "Returning to $CURRENT..."
git checkout -f "$CURRENT" 2>/dev/null || git checkout -f "$CURRENT"

echo "Done. Public repo is up to date."
