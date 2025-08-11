import json
import platform
import subprocess
from pathlib import Path


def test_pyinstaller_extract(tmp_path):
    dist_dir = tmp_path / "dist"
    build_dir = tmp_path / "build"
    spec_dir = tmp_path / "spec"
    system = platform.system().lower()
    system_label = "macos" if system == "darwin" else system
    machine = platform.machine().lower()
    sep = ";" if system.startswith("win") else ":"
    name = f"bankcleanr-{system_label}-{machine}"
    schema = Path("bankcleanr/schemas/transaction_v1.json").resolve()
    subprocess.run(
        [
            "pyinstaller",
            "--name",
            name,
            "--onefile",
            "--add-data",
            f"{schema}{sep}schemas",
            "--collect-submodules",
            "bankcleanr.parsers",
            "--hidden-import",
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
    exe = dist_dir / (name + (".exe" if system.startswith("win") else ""))
    sample_pdf = Path("Redacted bank statements/22b583f5-4060-44eb-a844-945cd612353c (1).pdf")
    out_jsonl = tmp_path / "out.jsonl"
    subprocess.run([str(exe), "extract", str(sample_pdf), str(out_jsonl), "--bank", "coop"], check=True)
    assert out_jsonl.exists()
    lines = out_jsonl.read_text().strip().splitlines()
    assert lines
    first = json.loads(lines[0])
    assert {"date", "description", "amount", "balance"} <= first.keys()

