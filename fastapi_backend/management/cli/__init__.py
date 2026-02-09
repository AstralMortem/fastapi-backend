from cyclopts import App

def _get_cmd(func_name: str):
    return f"fastapi_backend.management.cli.commands:{func_name}"

cli = App(name="fastapi_backend")

cli.command(_get_cmd("startproject"))