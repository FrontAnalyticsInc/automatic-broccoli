#!/usr/bin/env python

from sqlalchemy import create_engine
import pandas as pd
import config


class DBInterface(object):
    """Helper class for db access"""

    def __init__(self, database_uri=None):
        if not database_uri:
            self.engine = create_engine(config.IN_USE.SQLALCHEMY_DATABASE_URI)
        else:
            self.engine = create_engine(database_uri)

    def load_from_table(self, table_name=None, where=None) -> pd.DataFrame:
        """Loads all data (or data matching where statement) from the database and returns a pandas dataframe.

        Args:
            table_name: name of table in SQLite db
            where: SQL where statement query option

        Return:
            pandas Dataframe
        """
        if not table_name:
            raise Exception("Missing table name.")

        if not where:
            where = ""

        df = pd.read_sql_query("SELECT * FROM " + table_name + " " + where, con=self.engine)
        return df

    def save_to_table(self, df, table_name=None, replace_or_append=config.IN_USE.DB_WRITE_MODE, verbose=False):
        """Save a pandas dataframe into a SQLite table
        Args:
            df: Pandas dataframe to save to table
            table_name: str, name of table in SQLite db
            replace_or_append: str, option on how to save the new data, default=replace
            verbose: bool, print feedback, default=False
        Return:
            None
        """
        if not table_name:
            raise Exception("Missing table name.")

        df.to_sql(name=table_name, con=self.engine, if_exists=replace_or_append, index=False)
        if verbose:
            print("Saved to {}".format(table_name))
        return None
