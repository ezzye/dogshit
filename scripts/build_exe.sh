#!/usr/bin/env bash
set -euo pipefail

OUTDIR=${OUTDIR:-dist}
TARGETS=${TARGETS:-linux macos windows}
APP=bankcleanr

mkdir -p "$OUTDIR"

build_linux() {
  pyinstaller --clean --onefile -n "$APP" -p . bankcleanr/__main__.py \
    --distpath "$OUTDIR/linux"
}

build_macos() {
  pyinstaller --clean --onefile -n "$APP" -p . bankcleanr/__main__.py \
    --distpath "$OUTDIR/macos" --target-arch universal2
}

build_windows() {
  pyinstaller --clean --onefile -n "$APP.exe" -p . bankcleanr/__main__.py \
    --distpath "$OUTDIR/windows" --windowed
}

for t in $TARGETS; do
  case "$t" in
    linux) build_linux ;;
    mac*|darwin) build_macos ;;
    win*|windows) build_windows ;;
    *) echo "Unknown target $t"; exit 1 ;;
  esac
done

echo "Executables placed in $OUTDIR"
