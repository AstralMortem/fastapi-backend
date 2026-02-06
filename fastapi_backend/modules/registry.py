import sys
from collections import defaultdict
import warnings
from .config import ModuleConfig
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi_backend.db.model import Model


class ModulesRegistry:
    def __init__(self, installed_modules: tuple | None = None):

        if installed_modules is None and hasattr(sys.modules[__name__], "modules"):
            raise RuntimeError("You must supply an installed_modules argument.")

        self.all_models: dict[str, dict[str, "Model"]] = defaultdict(dict)
        self.module_configs: dict[str, ModuleConfig] = {}

        self.ready = False

        if installed_modules is not None:
            self.populate(installed_modules)

    def populate(self, installed_modules=None):
        if self.ready:
            return

        for entry in installed_modules:
            if isinstance(entry, ModuleConfig):
                module_config = entry
            else:
                module_config = ModuleConfig.create(entry)

            if module_config.label in self.module_configs:
                raise RuntimeError(
                    f"Module label arent unique, duplicates: {module_config.label}"
                )

            self.module_configs[module_config.label] = module_config
            module_config.reg = self

        for module_config in self.module_configs.values():
            module_config.import_models()

        tasks = []
        for module_config in self.module_configs.values():
            tasks.append(module_config.ready())

        asyncio.gather(*tasks)

        self.ready = True

    def register_model(self, module_label: str, model):
        model_name = model.__name__
        module_models = self.all_models[module_label]

        if model_name in module_models:
            if (
                model.__name__ == module_models[model_name].__name__
                and model.__module__ == module_models[model_name].__module__
            ):
                warnings.warn(
                    "Model '%s.%s' was already registered. Reloading models is not "
                    "advised as it can lead to inconsistencies, most notably with "
                    "related models." % (module_label, model_name),
                    RuntimeWarning,
                    stacklevel=2,
                )
            else:
                raise RuntimeError(
                    "Conflicting '%s' models in application '%s': %s and %s."
                    % (model_name, module_label, module_models[model_name], model)
                )

        module_models[model_name] = model

    def get_containing_module_config(self, obj_name: str) -> ModuleConfig:
        candidates = []
        for module_config in self.module_configs.values():
            if obj_name.startswith(module_config.name):
                subpath = obj_name.removeprefix(module_config.name)
                if subpath == "" or subpath[0] == ".":
                    candidates.append(module_config)
        if candidates:
            return sorted(candidates, key=lambda ac: -len(ac.name))[0]

    def get_module_config(self, module_label: str):
        cfg = self.module_configs.get(module_label, None)
        if cfg is None:
            raise ValueError(f"Config for {module_label} module not found")
        return cfg
    
    def get_module_models(self, module_label: str):
        return self.get_module_config(module_label).models
        
    def get_model(self, module_label: str, model_name: str):
        model = self.all_models.get(module_label, {}).get(model_name, None)
        if model is None:
            raise ValueError(f"Model {model_name} not found in module {module_label}")
        return model

modules = ModulesRegistry(None)
