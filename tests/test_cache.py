"""
Tests for :mod:`quiltwright.cache`.

The point of this module is that every runtime download agrees on one
location, and that the location is the platform's own -- not the XDG layout
that only happens to be right on Linux.  Both properties are checked here,
along with the per-dataset environment overrides.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quiltwright import cache


@pytest.fixture
def no_platformdirs(monkeypatch):
    """Simulate a core install, where platformdirs is not present."""
    real_import = __import__

    def _blocked(name, *args, **kwargs):
        if name == "platformdirs":
            raise ImportError("platformdirs disabled for this test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _blocked)


# ---------------------------------------------------------------------------
# cache_root
# ---------------------------------------------------------------------------


def test_cache_root_prefers_platformdirs(monkeypatch):
    """platformdirs decides the root, so macOS/Windows get native paths."""
    import platformdirs

    monkeypatch.setattr(platformdirs, "user_cache_dir", lambda app: f"/somewhere/{app}")
    assert cache.cache_root() == Path("/somewhere/quiltwright")


def test_cache_root_is_native_on_macos():
    """Guard the actual reason this module exists: macOS is not ~/.cache."""
    platformdirs = pytest.importorskip("platformdirs")
    from platformdirs.macos import MacOS

    macos_root = Path(MacOS(appname="quiltwright").user_cache_dir)
    assert "Library/Caches" in str(macos_root)
    assert ".cache" not in str(macos_root)
    assert platformdirs  # referenced so the import is not flagged as unused


def test_cache_root_falls_back_to_xdg(tmp_path, monkeypatch, no_platformdirs):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert cache.cache_root() == tmp_path / "xdg" / "quiltwright"


def test_cache_root_falls_back_to_home(tmp_path, monkeypatch, no_platformdirs):
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setattr(cache.Path, "home", classmethod(lambda _cls: tmp_path))
    assert cache.cache_root() == tmp_path / ".cache" / "quiltwright"


def test_cache_root_does_not_create_anything(tmp_path, monkeypatch, no_platformdirs):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert not cache.cache_root().exists()


# ---------------------------------------------------------------------------
# dataset_cache_dir
# ---------------------------------------------------------------------------


def test_dataset_cache_dir_nests_under_the_root(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "cache_root", lambda: tmp_path / "root")
    assert cache.dataset_cache_dir("tvb") == tmp_path / "root" / "tvb"
    assert cache.dataset_cache_dir("allen_ccf") == tmp_path / "root" / "allen_ccf"


def test_dataset_cache_dir_honours_its_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("QUILTWRIGHT_TEST_CACHE", str(tmp_path / "elsewhere"))
    resolved = cache.dataset_cache_dir("tvb", env_var="QUILTWRIGHT_TEST_CACHE")
    assert resolved == tmp_path / "elsewhere"


def test_dataset_cache_dir_ignores_other_datasets_env_vars(tmp_path, monkeypatch):
    """Relocating one dataset must not move the others."""
    monkeypatch.setattr(cache, "cache_root", lambda: tmp_path / "root")
    monkeypatch.setenv("QUILTWRIGHT_TVB_CACHE", str(tmp_path / "moved"))
    assert cache.dataset_cache_dir("tvb", env_var="QUILTWRIGHT_TVB_CACHE") == tmp_path / "moved"
    assert (
        cache.dataset_cache_dir("allen_ccf", env_var="QUILTWRIGHT_ALLEN_CACHE")
        == tmp_path / "root" / "allen_ccf"
    )


def test_dataset_cache_dir_expands_user_in_override(monkeypatch):
    monkeypatch.setenv("QUILTWRIGHT_TEST_CACHE", "~/somewhere")
    resolved = cache.dataset_cache_dir("tvb", env_var="QUILTWRIGHT_TEST_CACHE")
    assert "~" not in str(resolved)
    assert resolved.is_absolute()


def test_dataset_cache_dir_creates_only_on_request(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "cache_root", lambda: tmp_path / "root")
    assert not cache.dataset_cache_dir("tvb").exists()
    created = cache.dataset_cache_dir("tvb", create=True)
    assert created.is_dir()


def test_empty_env_var_falls_through_to_the_default(tmp_path, monkeypatch):
    """An unset-but-present empty variable must not resolve to the cwd."""
    monkeypatch.setattr(cache, "cache_root", lambda: tmp_path / "root")
    monkeypatch.setenv("QUILTWRIGHT_TEST_CACHE", "")
    resolved = cache.dataset_cache_dir("tvb", env_var="QUILTWRIGHT_TEST_CACHE")
    assert resolved == tmp_path / "root" / "tvb"
