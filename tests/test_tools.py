from tools import calculator, list_workspace, read_file, write_file


def test_calculator_basic():
    assert calculator("2 + 2") == "4"
    assert calculator("(3 + 4) * 2") == "14"


def test_calculator_rejects_unsafe():
    out = calculator("__import__('os').system('echo hi')")
    assert out.startswith("erreur:")


def test_write_then_read_roundtrip(tmp_path, monkeypatch):
    import tools

    monkeypatch.setattr(tools, "WORKSPACE", tmp_path)
    write_file("note.txt", "bonjour")
    assert read_file("note.txt") == "bonjour"
    assert "note.txt" in list_workspace()


def test_read_missing_file(tmp_path, monkeypatch):
    import tools

    monkeypatch.setattr(tools, "WORKSPACE", tmp_path)
    assert read_file("absent.txt").startswith("erreur:")


def test_path_escape_blocked(tmp_path, monkeypatch):
    import tools

    monkeypatch.setattr(tools, "WORKSPACE", tmp_path)
    out = write_file("../escape.txt", "x")
    assert out.startswith("erreur:")


def test_sibling_dir_with_same_prefix_blocked(tmp_path, monkeypatch):
    import tools

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (tmp_path / "workspace-evil").mkdir()
    monkeypatch.setattr(tools, "WORKSPACE", workspace)
    out = write_file("../workspace-evil/pwned.txt", "x")
    assert out.startswith("erreur:")
    assert not (tmp_path / "workspace-evil" / "pwned.txt").exists()
    (tmp_path / "workspace-evil" / "secret.txt").write_text("secret")
    assert read_file("../workspace-evil/secret.txt").startswith("erreur:")
