from cyclopts import App
from fastapi_backend import setup
from .discover import autodiscover


def cli():
    setup()

    cli_app = App()
    commands = autodiscover()

    core_cmds = commands.pop("fastapi_backend", None)
    if core_cmds:
        cli_app.command(core_cmds, name="*")
    for group, app in commands.items():
        cli_app.command(group)(app)

    cli_app()
