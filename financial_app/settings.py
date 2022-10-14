from pydantic import BaseSettings, Field


class Settings(BaseSettings):

    DB_URI: str = Field(env="DB_URI")


class TrainingSettings(Settings):

    MODEL_URI: str = Field(env="MODEL_URI")


class ServingSettings(Settings):
    RIDGE_MODEL_URI: str = Field(
        "http://127.0.0.1:5000/invocations",
        env="RIDGE_MODEL_URI"
    )

    LASSO_MODEL_URI = Field(
        "http://127.0.0.1:5001/invocations",
        env="LASSO_MODEL_URI"
    )

    @property
    def async_db_uri(self):
        return self.DB_URI.replace("sqlite", "sqlite+aiosqlite")
