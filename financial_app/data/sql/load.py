import argparse

import pandas as pd
from sqlalchemy import create_engine

from financial_app.settings import Settings


def load_data(db_uri: str, fl_loc: str, table_loc: str):
    """

    :param db_uri:
    :param fl_loc:
    :param table_loc:
    :return:
    """

    engine = create_engine(db_uri)

    data = pd.read_parquet(fl_loc)

    data.to_sql(table_loc, engine, index_label="id")


if __name__ == "__main__":

    settings = Settings()

    parser = argparse.ArgumentParser()

    parser.add_argument("--dataLoc")
    parser.add_argument("--tableName")

    args = parser.parse_args()

    load_data(settings.DB_URI, args.dataLoc, args.tableName)
