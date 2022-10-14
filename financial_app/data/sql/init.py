from sqlalchemy import create_engine

from financial_app.settings import Settings
from financial_app.data.sql.orm import Base

if __name__ == "__main__":

    settings = Settings()

    engine = create_engine(settings.DB_URI)

    Base.metadata.create_all(engine, checkfirst=True)
