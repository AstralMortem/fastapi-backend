MANAGE_PY_TEMPLATE = """#!/usr/bin/env python
#Django's command-line utility for administrative tasks

import os
import sys

def main():
    os.environ.setdefault("${settings_env}", "${project_name}.${settings_module_name}")
    try:
        from ${library_name}.management import cli
    except ImportError as e:
        raise ImportError(
            "Couldn't import FastAPI Backend. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from e

    cli()

if __name__ == "__main__":
    main()
"""

ASGI_PY_TEMPLATE = """#ASGI config.

import os
from ${library_name}.core.asgi import get_application

os.environ.setdefault("${settings_env}", "${settings_module_name}")

app = get_application()
"""

SETTINGS_PY_TEMLATE = """# Base Settings
from ${library_name}.conf import DefaultSettings
from pathlib import Path

class Settings(DefaultSettings):
    # Basic
    DEBUG: bool = True  # Change in production!!!

    #FS
    BASE_DIR: Path = Path(__file__).parent.parent

    #MODULES
    INSTALLED_MODULES: list[str] = []

    
# You can use this variable to get settings,
# or from ${library_name}.conf import settings
# there are the same reference
settings = Settings()
"""

MODULE_PY_TEMPLATE = """# ${module_name} module config
from fastapi_backend.modules import ModuleConfig

class ${module_name_camel}Config(ModuleConfig):
    name = "${module_name}"

"""

MODELS_PY_TEMPLATE = """from fastapi_backend.db import models

"""
