from pathlib import Path

import pytest

from fastapi_backend.management.fs import File, Folder


def test_file_render_creates_file_and_content(tmp_path: Path):
    file_node = File(
        "hello.txt",
        template="Hello ${name}",
        parent=tmp_path,
        params={"name": "Ada"},
    )

    rendered_path = file_node.render()

    assert rendered_path == tmp_path / "hello.txt"
    assert rendered_path.exists()
    assert rendered_path.read_text(encoding="utf-8") == "Hello Ada"


def test_file_render_from_template_path(tmp_path: Path):
    template_path = tmp_path / "template.txt"
    template_path.write_text("Value: ${value}", encoding="utf-8")

    file_node = File(
        "out.txt",
        template=template_path,
        parent=tmp_path,
        params={"value": "42"},
    )

    rendered_path = file_node.render()

    assert rendered_path == tmp_path / "out.txt"
    assert rendered_path.read_text(encoding="utf-8") == "Value: 42"


def test_folder_render_creates_nested_structure(tmp_path: Path):
    root = Folder(
        "root",
        parent=tmp_path,
        children=[
            File("a.txt", template="A"),
            Folder("sub", children=[File("b.txt", template="B")]),
        ],
    )

    rendered_path = root.render()

    assert rendered_path == tmp_path / "root"
    assert (tmp_path / "root" / "a.txt").read_text(encoding="utf-8") == "A"
    assert (tmp_path / "root" / "sub" / "b.txt").read_text(encoding="utf-8") == "B"

    sub_folder = root[1]
    assert isinstance(sub_folder, Folder)
    assert sub_folder.parent == tmp_path / "root"
    assert sub_folder.path == tmp_path / "root" / "sub"


def test_folder_dot_name_keeps_directory_empty(tmp_path: Path):
    root = Folder(".", parent=tmp_path)

    with pytest.raises(FileExistsError):
        rendered_path = root.render()
        assert rendered_path == tmp_path.resolve()
        assert list(tmp_path.iterdir()) == []


def test_render_into_existing_folder_same_name(tmp_path: Path):
    existing = tmp_path / "project"
    existing.mkdir()
    keep_file = existing / "keep.txt"
    keep_file.write_text("keep", encoding="utf-8")
    root = Folder("project", parent=tmp_path, children=[File("new.txt", template="new")])

    with pytest.raises(FileExistsError):
        _ = root.render()
        

    assert keep_file.read_text(encoding="utf-8") == "keep"
