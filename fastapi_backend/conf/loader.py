import threading
import sys
from typing import Any, ClassVar, Self
from pydantic_settings import BaseSettings
from .default import DefaultMixin
import os
import importlib
import warnings

warnings.filterwarnings(
    "ignore",
    message=r'Field name ".*" in ".*" shadows an attribute in parent ".*"',
    category=UserWarning,
)

SETTINGS_MODULE_ENV_VAR = "FASTAPI_SETTINGS_MODULE"

_autodiscover_lock = threading.Lock()
_autodiscover_done = False
_autodiscover_in_progress = False


def _autodiscover_once() -> None:
    """Try to discover user settings module from env (only once per process)."""
    global _autodiscover_done, _autodiscover_in_progress
    if _autodiscover_done or _autodiscover_in_progress:
        return
    with _autodiscover_lock:
        if _autodiscover_done or _autodiscover_in_progress:
            return
        module = os.getenv(SETTINGS_MODULE_ENV_VAR)
        if module:
            _autodiscover_in_progress = True
            try:
                importlib.import_module(module)
            finally:
                _autodiscover_in_progress = False
        _autodiscover_done = True


class DefaultSettings(DefaultMixin, BaseSettings):
    _singleton: ClassVar[Self] = None

    def __new__(cls, *args, **kwargs):
        _autodiscover_once()

        inst = DefaultSettings._singleton
        if inst is None:
            inst = super().__new__(cls)
            DefaultSettings._singleton = inst
            return inst

        # Upgrade singleton to newest subclass
        if inst.__class__ is not cls:
            # ensure subclass fields are built (important in pydantic v2)
            cls.model_rebuild(force=True)
            inst.__class__ = cls

        return inst

    def __init__(self, **values):
        # normal pydantic-settings init (env parsing/validation)
        super().__init__(**values)

        # Apply subclass defaults *only for real pydantic fields*
        cls = self.__class__
        for name, field in cls.model_fields.items():
            # Only override if the subclass explicitly defines a class default
            if name in cls.__dict__:
                object.__setattr__(self, name, getattr(cls, name))


def _expose_defaultsettings_to_package() -> None:
    # Avoid circular import issues when autodiscover imports a user module that
    # itself imports DefaultSettings from fastapi_backend.conf.
    pkg = sys.modules.get("fastapi_backend.conf")
    if pkg is not None and not hasattr(pkg, "DefaultSettings"):
        setattr(pkg, "DefaultSettings", DefaultSettings)


# module-level singleton
_expose_defaultsettings_to_package()
_autodiscover_once()
if DefaultSettings._singleton is None:
    settings = DefaultSettings()
else:
    settings = DefaultSettings._singleton
