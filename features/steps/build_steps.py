from behave import when, then
from pathlib import Path
import subprocess
import shutil
import os

@when("I run the build script")
def run_build_script(context):
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "build_exe.sh"
    context.build_dir = root / "dist" / "linux"
    if context.build_dir.exists():
        shutil.rmtree(context.build_dir)
    env = os.environ.copy()
    env["TARGETS"] = "linux"
    context.build_result = subprocess.run([
        "poetry",
        "run",
        "bash",
        str(script),
    ], cwd=root, capture_output=True, env=env)

@then("the build succeeds")
def build_succeeds(context):
    assert context.build_result.returncode == 0
    context.binary = context.build_dir / ("bankcleanr" + (".exe" if context.build_dir.name == "windows" else ""))
    assert context.binary.exists()

@then("the binary parses the sample PDF to jsonl")
def binary_parses(context):
    root = Path(__file__).resolve().parents[2]
    pdf = root / "Redacted bank statements" / "22b583f5-4060-44eb-a844-945cd612353c (1).pdf"
    context.jsonl_path = context.build_dir / "out.jsonl"
    if context.jsonl_path.exists():
        context.jsonl_path.unlink()
    result = subprocess.run([str(context.binary), "parse", str(pdf), "--jsonl", str(context.jsonl_path)], capture_output=True)
    context.parse_result = result
    assert result.returncode == 0
    assert context.jsonl_path.exists()

@then('the jsonl output contains "PAYPAL"')
def jsonl_contains(context):
    assert "PAYPAL" in context.jsonl_path.read_text()
