import inspect
import os
from types import ModuleType
from typing import TYPE_CHECKING
from fastapi_backend.utils.loaders import (
    import_module,
    module_has_submodule,
    import_string,
)
from pathlib import Path

if TYPE_CHECKING:
    from fastapi_backend.db.model import Model
    from .registry import ModulesRegistry

MODULE_PY_NAME = "modules"
MODELS_PY_NAME = "models"


def _path_from_py_module(module: ModuleType):
    """Attempt to determine app's filesystem path from its module."""
    # See #21874 for extended discussion of the behavior of this method in
    # various cases.
    # Convert to list because __path__ may not support indexing.
    paths = list(getattr(module, "__path__", []))
    if len(paths) != 1:
        filename = getattr(module, "__file__", None)
        if filename is not None:
            paths = [os.path.dirname(filename)]
        else:
            # For unknown reasons, sometimes the list returned by __path__
            # contains duplicates that must be removed (#25246).
            paths = list(set(paths))
    if len(paths) > 1:
        raise RuntimeError(
            "The module %r has multiple filesystem locations (%r); "
            "you must configure this app with an ModuleConfig subclass "
            "with a 'path' class attribute." % (module, paths)
        )
    elif not paths:
        raise RuntimeError(
            "The module %r has no filesystem location, "
            "you must configure this app with an ModuleConfig subclass "
            "with a 'path' class attribute." % module
        )
    return Path(paths[0]).resolve()


class ModuleConfig:
    def __init__(self, module_name: str, py_module: ModuleType):

        self.name: str = module_name
        self.py_module = py_module
        self.reg: "ModulesRegistry" = None

        if not hasattr(self, "label"):
            self.label = module_name.rpartition(".")[2]

        if not self.label.isidentifier():
            raise RuntimeError(
                "The module label '%s' is not a valid Python identifier." % self.label
            )

        if not hasattr(self, "path"):
            self.path = _path_from_py_module(py_module)

        self.models_py_module: ModuleType = None
        self.models: "list[Model]" = None

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.label)

    @classmethod
    def create(cls, entry: str):
        mod_cfg_cls = None
        module_name = None
        py_module = None

        try:
            py_module = import_module(entry)
        except Exception:
            pass
        else:
            if module_has_submodule(py_module, MODULE_PY_NAME):
                mod_path = f"{entry}.{MODULE_PY_NAME}"
                mod = import_module(mod_path)

                mod_configs = []

                for name, candidate in inspect.getmembers(mod, inspect.isclass):
                    if (
                        issubclass(candidate, cls)
                        and candidate is not cls
                        and getattr(candidate, "default", True)
                    ):
                        mod_configs.append((name, candidate))

                if len(mod_configs) > 1:
                    candidates = [repr(name) for name, _ in mod_configs]
                    raise RuntimeError(
                        "%r declares more than one default ModuleConfig: "
                        "%s." % (mod_path, ", ".join(candidates))
                    )
                else:
                    mod_cfg_cls = mod_configs[0][1]

        if mod_cfg_cls is None:
            mod_cfg_cls = cls
            module_name = entry

        if mod_cfg_cls is None:
            try:
                mod_cfg_cls = import_string(entry)
            except Exception:
                pass

        if module_name is None and mod_cfg_cls is None:
            mod_path, _, cls_name = entry.rpartition(".")
            if mod_path and cls_name[0].isupper():
                mod = import_module(mod_path)
        else:
            import_module(entry)

        if not issubclass(mod_cfg_cls, ModuleConfig):
            raise RuntimeError("isnt a subclass of ModuleConfig")

        if module_name is None:
            try:
                module_name = mod_cfg_cls.name
            except AttributeError:
                raise RuntimeError(f"{entry} Must suply name attribute")

        try:
            py_module = import_module(module_name)
        except ImportError:
            raise RuntimeError(
                "Cannot import '%s'. Check that '%s.%s.name' is correct."
                % (
                    module_name,
                    mod_cfg_cls.__module__,
                    mod_cfg_cls.__qualname__,
                )
            )

        return mod_cfg_cls(module_name, py_module)

    def import_models(self):
        self.models = self.reg.all_models[self.label]

        if module_has_submodule(self.py_module, MODELS_PY_NAME):
            models_module_name = f"{self.name}.{MODELS_PY_NAME}"
            self.models_py_module = import_module(models_module_name)

    async def ready(self):
        """
        Override this
        """
