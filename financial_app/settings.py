from pydantic import BaseSettings, Field


class Settings(BaseSettings):

    DB_URI: str = Field(env="DB_URI")


class TrainingSettings(Settings):

    MODEL_URI: str = Field(env="MODEL_URI")


class ServingSettings(Settings):

    @property
    def async_db_uri(self):
        return self.DB_URI.replace("sqlite", "sqlite+aiosqlite")
