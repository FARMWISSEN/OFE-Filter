#!/bin/bash
# Compile Qt translation source files (.ts) to binary (.qm).
#
# Usage (from Makefile):
#   scripts/compile-strings.sh <lrelease_binary> "de en"
#
# Translation files are expected as i18n/OFEFilter_<locale>.ts

set -e

LRELEASE=$1
LOCALES=$2

PLUGIN_TS_BASENAME="OFEFilter"

if [ -z "$LRELEASE" ]; then
  # Try to auto-detect if not provided.
  for CANDIDATE in lrelease lrelease-qt5; do
    if command -v "$CANDIDATE" >/dev/null 2>&1; then
      LRELEASE="$CANDIDATE"
      break
    fi
  done
fi

if [ -z "$LRELEASE" ] || ! command -v "$LRELEASE" >/dev/null 2>&1; then
  echo "ERROR: lrelease not found. Install Qt5 tools (often qttools5-dev-tools) or provide the binary as the first argument." >&2
  exit 1
fi

for LOCALE in ${LOCALES}
do
    TS_FILE="i18n/${PLUGIN_TS_BASENAME}_${LOCALE}.ts"
    if [ ! -f "$TS_FILE" ]; then
      echo "ERROR: Missing translation source file: $TS_FILE" >&2
      exit 1
    fi
    echo "Processing: ${PLUGIN_TS_BASENAME}_${LOCALE}.ts"
    "$LRELEASE" "$TS_FILE"
done
