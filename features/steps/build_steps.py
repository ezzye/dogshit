import os
import platform
import subprocess
import tempfile
from pathlib import Path

from behave import given, when, then  # type: ignore[import-untyped]

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@given("a temporary working directory for build")
def step_tmpdir(context):
    context.tmpdir = tempfile.TemporaryDirectory()
    context.cwd = Path(context.tmpdir.name)


@when("I run the bankcleanr build command")
def step_run_build(context):
    subprocess.run(
        ["python", "-m", "bankcleanr.cli", "build"],
        cwd=context.cwd,
        check=True,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
        stdin=subprocess.DEVNULL,
    )


@then("a bankcleanr executable is created")
def step_executable_created(context):
    system = platform.system().lower()
    system_label = "macos" if system == "darwin" else system
    machine = platform.machine().lower()
    name = f"bankcleanr-{system_label}-{machine}"
    exe = context.cwd / "dist" / (name + (".exe" if system.startswith("win") else ""))
    assert exe.exists()
    context.tmpdir.cleanup()
