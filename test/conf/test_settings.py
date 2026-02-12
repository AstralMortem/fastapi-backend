import importlib
import sys
import pytest

DEFAULT_DEBUG_VALUE = True
ENV_VAR = "FASTAPI_SETTINGS_MODULE"


def test_default_value_is_used():
    from fastapi_backend.conf import settings, DefaultSettings

    assert settings.DEBUG is DEFAULT_DEBUG_VALUE
    # triggers configure via singleton access
    _ = DefaultSettings()
    assert settings.DEBUG is DEFAULT_DEBUG_VALUE


def test_subclass_does_not_eagerly_override_until_instantiated():
    from fastapi_backend.conf import settings, DefaultSettings

    assert settings.DEBUG is DEFAULT_DEBUG_VALUE

    class A(DefaultSettings):
        DEBUG: bool = False

    # still lazy
    assert settings.DEBUG is DEFAULT_DEBUG_VALUE


def test_single_subclass_overrides_global_on_init_and_identity_preserved():
    from fastapi_backend.conf import DefaultSettings, settings

    assert settings.DEBUG is DEFAULT_DEBUG_VALUE  # default

    class A(DefaultSettings):
        DEBUG: bool = False
        PROJECT_VERSION: str = "1.0.0"

    # still old until instantiate
    assert settings.DEBUG is DEFAULT_DEBUG_VALUE

    a = A()  # triggers reconfigure + in-place mutation

    # assert a is settings
    assert settings.DEBUG is False


def test_multiple_subclasses_last_registered_wins():
    from fastapi_backend.conf import DefaultSettings, settings

    assert settings.DEBUG is DEFAULT_DEBUG_VALUE

    class A(DefaultSettings):
        DEBUG: bool = False

    settingsa = A()

    assert settings.DEBUG is False
    assert settingsa is settings

    class B(DefaultSettings):
        DEBUG: bool = True

    # not applied yet
    assert settings.DEBUG is False  # From A()
    assert settingsa.DEBUG is False

    settingsb = B()  # instantiate last one to trigger rebuild

    assert settings.DEBUG is True
    assert settingsb is settings
    assert settingsa is settings
    assert settingsa is settingsb


def test_settings_from_env_module():
    import os

    os.environ.setdefault(ENV_VAR, "test.conf.external_conf")

    from fastapi_backend.conf import settings

    assert settings.DEBUG is False
