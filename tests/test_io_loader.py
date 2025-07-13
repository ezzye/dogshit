import os
from pathlib import Path

import pytest

from bankcleanr.io import loader


def test_load_from_path_file(monkeypatch, tmp_path, capsys):
    called = []

    def fake_load(path):
        called.append(path)
        return ["tx"]

    monkeypatch.setattr(loader, "load_transactions", fake_load)
    pdf = tmp_path / "file.pdf"
    pdf.write_text("dummy")

    result = loader.load_from_path(str(pdf), verbose=True)
    captured = capsys.readouterr()
    assert result == ["tx"]
    assert called == [str(pdf)]
    assert str(pdf) in captured.out


def test_load_from_path_directory(monkeypatch, tmp_path, capsys):
    order = []

    def fake_load(path):
        order.append(Path(path).name)
        return [path]

    monkeypatch.setattr(loader, "load_transactions", fake_load)

    (tmp_path / "b.pdf").write_text("b")
    (tmp_path / "a.pdf").write_text("a")

    result = loader.load_from_path(str(tmp_path), verbose=True)
    captured = capsys.readouterr()
    assert order == ["a.pdf", "b.pdf"]
    assert result == [str(tmp_path / "a.pdf"), str(tmp_path / "b.pdf")]
    assert str(tmp_path / "a.pdf") in captured.out
    assert str(tmp_path / "b.pdf") in captured.out
