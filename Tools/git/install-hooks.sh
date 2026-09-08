#!/usr/bin/env bash
# Install the Nextcore isolated-asset guard into the local .git/hooks directory.
# Idempotent. Does not touch hooks that are unrelated to this guard.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
hooks_dir="$(git -C "$repo_root" rev-parse --path-format=absolute --git-path hooks)"
mkdir -p "$hooks_dir"

template="$repo_root/Tools/git/hooks/pre-commit"
target="$hooks_dir/pre-commit"

if [ ! -f "$template" ]; then
    echo "ERROR: missing pre-commit template at $template" >&2
    exit 1
fi

if [ -e "$target" ] && [ ! -f "$target" ]; then
    echo "ERROR: $target exists and is not a regular file" >&2
    exit 1
fi

# Always overwrite so the guard matches the current template.
# Existing user-installed hooks (e.g. commit signing, lint) are NOT combined
# here; the guard is the only purpose of this file.
cp -f "$template" "$target"
chmod +x "$target"

echo "Installed pre-commit isolated-asset guard at $target"
