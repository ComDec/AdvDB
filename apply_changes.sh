#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 /abs/path/to/root /path/to/changes.patch" >&2
  exit 1
fi

ROOT="$(cd "$1" && pwd)"
PATCH_FILE="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
TARGET_FILE="$ROOT/transaction_manager.py"

if [[ ! -f "$PATCH_FILE" ]]; then
  echo "Missing patch file: $PATCH_FILE" >&2
  exit 1
fi

if [[ ! -f "$TARGET_FILE" ]]; then
  echo "Missing target file: $TARGET_FILE" >&2
  exit 1
fi

patch -p1 -d "$ROOT" < "$PATCH_FILE"

