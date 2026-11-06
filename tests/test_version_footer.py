"""/api/version feeds the GUI footer ("MeCoBi v… @ commit · last updated <date>")."""

import importlib


def _fresh_info(monkeypatch, git_ok):
    mod = importlib.import_module("mecobi.web.app")  # the module, not the FastAPI instance
    monkeypatch.setattr(mod, "_VERSION_INFO", None)
    if not git_ok:  # the Docker image: no .git, so git calls fail
        import subprocess

        def boom(*a, **k):
            raise FileNotFoundError("git")
        monkeypatch.setattr(subprocess, "run", boom)
    return mod._version_info()


def test_image_without_git_uses_the_build_args(monkeypatch):
    monkeypatch.setenv("MECOBI_COMMIT", "0123456789abcdef")
    monkeypatch.setenv("MECOBI_BUILD_DATE", "2026-10-02")
    info = _fresh_info(monkeypatch, git_ok=False)
    assert info["commit"] == "0123456" and info["updated"] == "2026-10-02"
    assert info["branch"] is None


def test_no_git_and_no_build_args_leaves_fields_empty(monkeypatch):
    monkeypatch.delenv("MECOBI_COMMIT", raising=False)
    monkeypatch.delenv("MECOBI_BUILD_DATE", raising=False)
    info = _fresh_info(monkeypatch, git_ok=False)
    assert info["commit"] is None and info["updated"] is None and info["version"]
