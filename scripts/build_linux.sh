#!/usr/bin/env bash
set -euo pipefail

docker run --rm -v "$PWD":/app -w /app python:3.12-slim bash -c "pip install . jsonschema pyinstaller && python -m bankcleanr.cli build"
