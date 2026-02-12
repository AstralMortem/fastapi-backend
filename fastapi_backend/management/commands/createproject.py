from pathlib import Path
from fastapi_backend.management.cli.command import BaseCommand
from cyclopts import Parameter
from typing import Annotated
import string


def validate_name(type_, value: str):
    if any(value.startswith(x) for x in string.punctuation + string.digits):
        raise ValueError("Invalid name")


class Command(BaseCommand):
    help = "Create project command"

    def handle(
        self,
        name: Annotated[str, Parameter(validator=validate_name, help="Project name")],
        path: Annotated[Path, Parameter(required=False, help="Project path")],
    ):
        from fastapi_backend.management.fs import create_project

        try:
            res = create_project(name, path)
            return f"[green]Project created successfuly: {res.path}[/green]"
        except Exception as e:
            return f"[red]{e}[/red]"
