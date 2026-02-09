from pathlib import Path
from cyclopts import Parameter

from typing import Annotated


PROJ_NAME = Annotated[str, Parameter(help="Project folder name", required=True)]
PROJ_PATH = Annotated[Path | None, Parameter(name=["-p", "--path"], help="Project folder path", required=False)]

def startproject(name: PROJ_NAME, path: PROJ_PATH = None):
    from fastapi_backend.management.fs import create_project
    create_project(name, path)