from pathlib import Path
from cyclopts import Parameter
import string

from typing import Annotated


PROJ_NAME = Annotated[str, Parameter(help="Project folder name", required=True)]
PROJ_PATH = Annotated[Path | None, Parameter(name=["-p", "--path"], help="Project folder path", required=False)]

def _check_name(name: str):
    allowed = string.ascii_letters + "_"
    res = all([x in allowed for x in name])
    if not res:
        raise ValueError("Invalud name, only ASCII and _ symbol supported")
        

def createproject(name: PROJ_NAME, path: PROJ_PATH = None):
    from fastapi_backend.management.fs import create_project

    try:
        _check_name(name)
        res = create_project(name, path)
        return f"[green]Project created successfuly: {res.path}[/green]"
    except Exception as e:
        return f"[red]{e}[/red]"
    


def addmodule(
        name: Annotated[str, Parameter(help="App name", required=True)],
    ):
    from fastapi_backend.management.fs import create_module
    from fastapi_backend.conf import settings

    try:
        _check_name(name)
        res = create_module(name, settings.BASE_DIR)
        return f"[green]Module successfuly created: {res.path}[/green]"
    except Exception as e:
        return f"[red]{e}[/red]"

