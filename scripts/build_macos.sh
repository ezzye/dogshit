#!/usr/bin/env bash
set -euo pipefail

pip install . jsonschema pyinstaller
python -m bankcleanr.cli build
