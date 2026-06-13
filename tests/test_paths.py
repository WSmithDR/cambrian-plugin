from pathlib import Path

from lib import paths


def test_data_dir_honors_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CAMBRIAN_DATA_DIR", str(tmp_path / "custom"))
    assert paths.data_dir() == tmp_path / "custom"


def test_data_dir_default_when_unset(monkeypatch):
    monkeypatch.delenv("CAMBRIAN_DATA_DIR", raising=False)
    assert paths.data_dir() == Path.home() / ".local" / "share" / "cambrian"


def test_corpus_file_path(tmp_path, monkeypatch):
    monkeypatch.setenv("CAMBRIAN_DATA_DIR", str(tmp_path))
    assert paths.corpus_file("docker") == tmp_path / "corpus" / "docker.jsonl"


def test_slugify():
    assert paths.slugify("Aprender Docker!") == "aprender-docker"
    assert paths.slugify("  GraphQL  vs  REST ") == "graphql-vs-rest"
    assert paths.slugify("") == "untitled"
