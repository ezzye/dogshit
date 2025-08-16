#!/usr/bin/env pwsh
Set-StrictMode -Version Latest

pip install . jsonschema pyinstaller
python -m bankcleanr.cli build
