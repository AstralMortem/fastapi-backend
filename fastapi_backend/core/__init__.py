def get_application():
    from fastapi_backend import setup
    from .asgi import create_app

    setup()
    return create_app()
