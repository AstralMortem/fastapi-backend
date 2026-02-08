import os
import sys
import pytest


ENV_VAR = "FASTAPI_SETTINGS_MODULE"


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    # ensure clean settings state per test
    os.environ.pop(ENV_VAR, None)

    # force fresh imports so module-level singletons are rebuilt per test
    sys.modules.pop("fastapi_backend.conf", None)
    sys.modules.pop("fastapi_backend.conf.loader", None)

    yield

    # keep env clean for any subsequent imports
    os.environ.pop(ENV_VAR, None)
    sys.modules.pop("fastapi_backend.conf", None)
    sys.modules.pop("fastapi_backend.conf.loader", None)
