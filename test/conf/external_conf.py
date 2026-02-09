from fastapi_backend.conf import DefaultSettings


class ExternalModuleSettings(DefaultSettings):
    DEBUG: bool = False
    

settings = ExternalModuleSettings()
