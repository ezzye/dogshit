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
  local arch="${MACOS_ARCH:-universal2}"
  if [[ "$arch" == "universal2" ]]; then
    local pybin
    pybin=$(command -v python3)
    if ! file "$pybin" | grep -q "arm64" || ! file "$pybin" | grep -q "x86_64"; then
      echo "Error: python3 at $pybin is not a universal build" >&2
      echo "Install the universal macOS installer from python.org or set MACOS_ARCH=arm64" >&2
      exit 1
    fi
  fi
  pyinstaller --clean --onefile -n "$APP" -p . bankcleanr/__main__.py \
    --distpath "$OUTDIR/macos" --target-arch "$arch"
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
