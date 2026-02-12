from pathlib import Path
from pydantic import Field, AnyUrl, field_validator
from typing import Literal


_SUPPORTED_DB_PROVIDER = Literal["postgresql", "sqlite"]
_SUPPORTED_DB_DRIVER = Literal["psycopg2"]
_SUPPORTED_DB_ASYNC_DRIVER = Literal["aiosqlite", "asyncpg"]

_DB_PROVIDER_DRIVER_MAP = {
    "sqlite": {"sync": [None], "async": ["aiosqlite"]},
    "postgresql": {"sync": ["psycopg"], "async": ["asyncpg"]},
}


def _default_driver(env: dict, mode: Literal["sync", "async"]):
    provider: _SUPPORTED_DB_PROVIDER = env["DB_PROVIDER"]
    maped = _DB_PROVIDER_DRIVER_MAP.get(provider, None)
    if not maped:
        return None
    if len(maped[mode]):
        return maped[mode][0]
    return None


def _validate_driver_field(field, info, mode: Literal["sync", "async"]):
    provider: _SUPPORTED_DB_PROVIDER = info.data.get("DB_PROVIDER")
    maped = _DB_PROVIDER_DRIVER_MAP.get(provider, None)
    if not maped:
        raise ValueError("Invalid DB_DRIVER")

    valid_fields = maped[mode]

    if field not in valid_fields:
        raise ValueError(
            f"Inavlid sync driver for {provider} DB Provider, supported: {', '.join(valid_fields)}"
        )
    return field


def _build_db_url(env: dict, mode: Literal["sync", "async"]):
    provider: _SUPPORTED_DB_PROVIDER = env.get("DB_PROVIDER")

    schema = provider
    if mode == "sync":
        if driver := env.get("DB_DRIVER", None):
            schema += f"+{driver}"
    elif mode == "async":
        if driver := env.get("DB_ASYNC_DRIVER", None):
            schema += f"+{driver}"

    host = env.get("BASE_DIR", None)
    if host is not None:
        host = "/" + str(Path(host, "db.sqlite").relative_to(host))
    else:
        host = "127.0.0.1"

    return AnyUrl.build(
        scheme=schema,
        host=host,
        port=int(env.get("DB_PORT", None) or 0) or None,
        username=env.get("DB_USER", None),
        password=env.get("DB_PASSWORD", None),
        path=env.get("DB_NAME", None),
    )


class DefaultMixin:
    # GENERAL
    DEBUG: bool = True
    PROJECT_NAME: str = "FastAPI Project"
    PROJECT_VERSION: str = "0.0.1"

    # FS
    BASE_DIR: Path = Path(__file__).parent.parent

    # DATABASE
    DB_PROVIDER: _SUPPORTED_DB_PROVIDER = "sqlite"
    DB_DRIVER: _SUPPORTED_DB_DRIVER | None = Field(
        default_factory=lambda e: _default_driver(e, "sync")
    )
    DB_ASYNC_DRIVER: _SUPPORTED_DB_ASYNC_DRIVER | None = Field(
        default_factory=lambda e: _default_driver(e, "async")
    )
    DB_HOST: str | None = "/sqlite.db"
    DB_PORT: int | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_NAME: str | None = None
    DATABASE_URL: AnyUrl = Field(default_factory=lambda e: _build_db_url(e, "sync"))
    DATABASE_ASYNC_URL: AnyUrl = Field(
        default_factory=lambda e: _build_db_url(e, "async")
    )

    @field_validator("DB_DRIVER")
    @classmethod
    def validate_sync_driver(cls, v, info):
        return _validate_driver_field(v, info, "sync")

    @field_validator("DB_ASYNC_DRIVER")
    @classmethod
    def validate_async_driver(cls, v, info):
        return _validate_driver_field(v, info, "async")

    # MODULES
    INSTALLED_MODULES: list[str] = []
