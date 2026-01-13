from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(validate_default=False)
    intempus_api_user: str
    intempus_api_key: str
    db_name: str