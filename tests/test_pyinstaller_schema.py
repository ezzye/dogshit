import subprocess
import sys
from pathlib import Path


def test_schema_bundled_with_pyinstaller(tmp_path):
    dist_dir = tmp_path / "dist"
    build_dir = tmp_path / "build"
    spec_dir = tmp_path / "spec"
    subprocess.run(
        [
            "pyinstaller",
            "--name",
            "bankcleanr",
            "--onefile",
            "--collect-data",
            "bankcleanr.schemas",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(build_dir),
            "--specpath",
            str(spec_dir),
            "bankcleanr/cli.py",
        ],
        check=True,
    )
    executable = dist_dir / ("bankcleanr.exe" if sys.platform.startswith("win") else "bankcleanr")
    result = subprocess.run([str(executable), "--help"], check=True, capture_output=True, text=True)
    assert "Usage" in result.stdout
