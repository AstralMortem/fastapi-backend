def setup():
    from fastapi_backend.modules import modules
    from fastapi_backend.conf import settings

    modules.populate(settings.INSTALLED_MODULES)
