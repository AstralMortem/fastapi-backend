from fastapi_backend.conf.loader import DefaultSettings


class ExternalModuleSettings(DefaultSettings):
    DEBUG: bool = False
    

settings = ExternalModuleSettings()
