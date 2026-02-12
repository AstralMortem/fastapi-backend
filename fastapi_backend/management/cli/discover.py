import importlib
import pkgutil
import inspect
from cyclopts import App
from .command import BaseCommand
from fastapi_backend.management import commands
from fastapi_backend.utils.loaders import module_has_submodule, import_module


def autodiscover():
    import fastapi_backend
    from fastapi_backend.modules import modules, ModuleConfig

    sub_commands = {}

    allowed_modules = list(modules.module_configs.values()) + [
        ModuleConfig("fastapi_backend", fastapi_backend)
    ]

    for cfg in allowed_modules:
        if cfg.commands_module is None:
            continue
        if not hasattr(cfg.commands_module, "__path__"):
            continue

        app = App(
            name=cfg.label,
            alias=getattr(cfg.commands_module, "alias", None),
            help=getattr(cfg.commands_module, "help", ""),
        )

        for _, mod_name, _ in pkgutil.iter_modules(cfg.commands_module.__path__):
            if module_has_submodule(cfg.commands_module, mod_name):
                mod = import_module(f"{cfg.commands_module.__name__}.{mod_name}")
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, BaseCommand) and obj is not BaseCommand:
                        obj(app)

        sub_commands[cfg.label] = app

    return sub_commands
