import os
import platform
import shutil
import subprocess
from pathlib import Path

import pytest


if shutil.which("pyinstaller") is None:
    pytest.skip(
        "PyInstaller is not installed; skipping PyInstaller integration tests.",
        allow_module_level=True,
    )


def test_schema_bundled_with_pyinstaller(tmp_path):
    system = platform.system().lower()
    system_label = "macos" if system == "darwin" else system
    machine = platform.machine().lower()
    name = f"bankcleanr-{system_label}-{machine}"
    subprocess.run(
        ["python", "-m", "bankcleanr.cli", "build"],
        cwd=tmp_path,
        check=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
        stdin=subprocess.DEVNULL,
    )
    executable = tmp_path / "dist" / (name + (".exe" if system.startswith("win") else ""))
    assert executable.exists()
    sample_pdf = Path("Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf")
    out_jsonl = tmp_path / "out.jsonl"
    subprocess.run([str(executable), "extract", str(sample_pdf), str(out_jsonl), "--bank", "coop"], check=True)
    assert out_jsonl.read_text()
