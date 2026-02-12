from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from mako.template import Template
from .fs_tempates import (
    MANAGE_PY_TEMPLATE,
    ASGI_PY_TEMPLATE,
    SETTINGS_PY_TEMLATE,
    MODULE_PY_TEMPLATE,
    MODELS_PY_TEMPLATE,
)
from fastapi_backend.utils.string import snake_to_camel


class File:
    def __init__(
        self,
        name: str,
        template: str | Path,
        parent: Path | None = None,
        params: dict[str, Any] | None = None,
    ):
        self.name = name
        self.parent = parent
        self.path = Path(parent or ".", name).resolve()
        self.template = template
        self.params = params or {}

    def render(
        self,
        params: dict[str, Any] | None = None,
        *,
        encoding: str = "utf-8",
    ) -> Path:
        context = {**self.params, **(params or {})}
        if isinstance(self.template, Path):
            template_text = self.template.read_text(encoding=encoding)
        else:
            template_text = self.template

        rendered = Template(template_text).render(**context)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(rendered, encoding=encoding)
        return self.path


class Folder(list["File | Folder"]):
    def __init__(
        self,
        name: str,
        parent: Path | None = None,
        children: Iterable[File | "Folder"] | None = None,
        params: dict[str, Any] | None = None,
    ):
        super().__init__(children or [])
        self.name = name
        self.parent = parent
        self.path = Path(parent or ".", name).resolve()
        self.params = params or {}

    def add(self, node: File | "Folder") -> "Folder":
        self.append(node)
        return self

    def render(self, params: dict[str, Any] | None = None) -> Path:
        context = {**self.params, **(params or {})}
        self.path.mkdir(parents=True, exist_ok=False)
        for node in self:
            if isinstance(node, Folder):
                node.parent = self.path
                node.path = (self.path / node.name).resolve()
                node.render(context)
            else:
                node.parent = self.path
                node.path = (self.path / node.name).resolve()
                node.render(context)
        return self.path


def create_project(name: str, path: Path | None = None):

    params = {
        "library_name": "fastapi_backend",
        "project_name": name,
        "settings_env": "FASTAPI_SETTINGS_MODULE",
        "settings_module_name": "settings",
    }

    root = Folder(name, path)
    root.append(File("manage.py", template=MANAGE_PY_TEMPLATE, params=params))

    core_folder = Folder(name)
    core_folder.append(File("__init__.py", template=""))
    core_folder.append(File("settings.py", template=SETTINGS_PY_TEMLATE, params=params))
    core_folder.append(File("asgi.py", template=ASGI_PY_TEMPLATE, params=params))
    root.append(core_folder)

    root.render()

    return root


def create_module(name: str, path: Path):

    params = {
        "module_name": name,
        "module_name_camel": snake_to_camel(name),
    }

    root = Folder(name, path)
    root.append(File("__init__.py", template=""))
    root.append(File("module.py", template=MODULE_PY_TEMPLATE, params=params))
    root.append(File("models.py", template=MODELS_PY_TEMPLATE))
    migrations = Folder("migrations")
    migrations.append(File("__init__.py", template=""))
    root.append(migrations)

    root.render()
    return root
