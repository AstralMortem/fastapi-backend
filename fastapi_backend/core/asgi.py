from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from fastapi_backend.conf import settings
from fastapi_backend.modules import modules


def create_app():

    app = FastAPI()

    # Register ORM Context
    register_tortoise(
        app,
        db_url=str(settings.DATABASE_ASYNC_URL),
        modules=modules.to_tortoise_modules(),
    )

    return app
