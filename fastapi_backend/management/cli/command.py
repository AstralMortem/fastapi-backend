from abc import ABC, abstractmethod
from cyclopts import App
from fastapi_backend.utils.string import camel_to_snake
from pathlib import Path


class BaseCommand(ABC):
    help: str | None = None
    name: str | None = None
    alias: str | None = None

    def __init__(self, app: App):
        self.app = app
        self.console = app.console
        self.app.command(
            self.handle,
            name=self.command_name,
            help=self.help or self.handle.__doc__,
            alias=self.alias,
        )

    @property
    def command_name(self):
        if not self.name:
            if self.__class__.__name__ == "Command":
                return self.__class__.__module__.rsplit(".")[-1]
            n = camel_to_snake(self.__class__.__name__)
            if n.endswith("_command"):
                return n.removesuffix("_command")
        return self.name

    @abstractmethod
    def handle(self, **options):
        raise NotImplementedError()
