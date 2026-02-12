from .createproject import validate_name
from fastapi_backend.management.cli.command import BaseCommand
from typing import Annotated
from cyclopts import Parameter


class Command(BaseCommand):
    help = "Create module inside project command"

    def handle(
        self,
        name: Annotated[str, Parameter(validator=validate_name, help="Module name")],
    ):
        from fastapi_backend.management.fs import create_module
        from fastapi_backend.conf import settings

        try:
            res = create_module(name, settings.BASE_DIR)
            return f"[green]Module successfuly created: {res.path}[/green]"
        except Exception as e:
            return f"[red]{e}[/red]"
