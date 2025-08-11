import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from behave import given, when, then  # type: ignore[import-untyped]

FIXTURES = {
    "coop": [
        Path("tests/fixtures/coop/statement_1.pdf"),
        Path("tests/fixtures/coop/statement_2.pdf"),
    ]
}


@given("a sample {bank} statement")
def step_given_sample(context, bank):
    fixtures = FIXTURES.get(bank)
    if not fixtures:
        raise NotImplementedError(f"No fixtures for bank {bank}")
    context.tmpdir = tempfile.TemporaryDirectory()
    fixture = fixtures[0]
    context.pdf_path = os.path.join(context.tmpdir.name, fixture.name)
    shutil.copy(fixture, context.pdf_path)


@when("I run the {bank} extractor")
def step_run_extractor(context, bank):
    context.jsonl_path = os.path.join(context.tmpdir.name, "out.jsonl")
    subprocess.run(
        [
            "python",
            "-m",
            "bankcleanr.cli",
            "extract",
            "--bank",
            bank,
            context.pdf_path,
            context.jsonl_path,
        ],
        check=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
        stdin=subprocess.DEVNULL,
    )


@when("I parse the {bank} statement")
def step_parse_statement(context, bank):
    context.jsonl_path = os.path.join(context.tmpdir.name, "out.jsonl")
    subprocess.run(
        [
            "python",
            "-m",
            "bankcleanr.cli",
            "parse",
            "--bank",
            bank,
            context.pdf_path,
            context.jsonl_path,
        ],
        check=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
        stdin=subprocess.DEVNULL,
    )


@then("a JSONL file with {count:d} transactions is created")
def step_then_check(context, count):
    with open(context.jsonl_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
    assert len(lines) == count
    context.tmpdir.cleanup()


@given("multiple {bank} statements")
def step_given_multiple(context, bank):
    fixtures = FIXTURES.get(bank)
    if not fixtures:
        raise NotImplementedError(f"No fixtures for bank {bank}")
    context.tmpdir = tempfile.TemporaryDirectory()
    context.pdf_dir = context.tmpdir.name
    for fixture in fixtures[:2]:
        shutil.copy(fixture, os.path.join(context.pdf_dir, fixture.name))


@when("I run the {bank} extractor on the directory")
def step_run_extractor_dir(context, bank):
    context.jsonl_path = os.path.join(context.tmpdir.name, "out.jsonl")
    subprocess.run(
        [
            "python",
            "-m",
            "bankcleanr.cli",
            "extract",
            "--bank",
            bank,
            context.pdf_dir,
            context.jsonl_path,
        ],
        check=True,
        env={**os.environ, "PYTHONPATH": os.getcwd()},
        stdin=subprocess.DEVNULL,
    )
