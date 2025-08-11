from importlib import util
from pathlib import Path


def test_cli_importable_in_isolation():
    """CLI module should import without package context."""
    cli_path = Path(__file__).resolve().parents[1] / "bankcleanr" / "cli.py"
    spec = util.spec_from_file_location("cli", cli_path)
    module = util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert hasattr(module, "app")
