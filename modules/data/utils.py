#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.data.utils

Common classes and functions to work with the SQLite3 database
"""

from os import path
import re
import sqlite3


def execute_sql(sql: str, db_path: str, parameters: tuple = None):
    """Execute SQL query on an SQLite database"""

    def dict_factory(cursor, row):
        """see https://docs.python.org/2/library/
        sqlite3.html#sqlite3.Connection.row_factory"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    with sqlite3.connect(db_path) as db_con:
        db_con.row_factory = dict_factory
        db_cur = db_con.cursor()
        if parameters:
            return db_cur.execute(sql, parameters)
        else:
            return db_cur.execute(sql)


class Database:
    """Wrapper class to do manipulation on an SQLite3 database file"""

    def __init__(self, db_path: str):
        """db_path: path to sqlite3 database file"""

        self.db_path = db_path

        # get schema information
        sql_schema = open(path.join(path.dirname(
            path.abspath(__file__)), "schema.sql"), "r").read()
        self.schema_ver = re.search(
            r"\n-- schema ver\.: (?P<ver>1\.0\.0)", sql_schema).group("ver")

        if path.exists(self.db_path):
            # check if existing one have the same schema version
            db_schema_ver = next(execute_sql(
                "SELECT * FROM schema WHERE 1", self.db_path))["ver"]
            if db_schema_ver != self.schema_ver:
                raise Exception(
                    "SQLite3 database exists but contains different schema " +
                    "version ({} rather than {}), exiting!".format(
                        db_schema_ver, self.schema_ver))
        else:
            # create new database
            with sqlite3.connect(self.db_path) as db_con:
                db_cur = db_con.cursor()
                db_cur.executescript(sql_schema)

    def query(self, sql: str, parameters: tuple = None):
        """query an SQL statement, return (dict-modified) results"""
        return execute_sql(sql, self.db_path, parameters)

    def select(self, table: str, clause: str,
               parameters: tuple = None, props: list = []):
        """execute a SELECT ... FROM ... WHERE"""

        if len(props) < 1:
            props_string = "*"
        else:
            props_string = ",".join(props)

        sql = "SELECT {} FROM {} {}".format(
            props_string,
            table,
            clause
        )
        return self.query(sql, parameters)

    def insert(self, table: str, data: dict):
        """execute an INSERT INTO ... VALUES ..."""

        keys = []
        values = []
        for key, value in data.items():
            if type(value) == bool:
                value = int(value)
            elif type(value) == str:
                value = "{}".format(value)
            elif value is None:
                value = "NULL"
            keys.append(str(key))
            values.append(str(value))

        sql = "INSERT INTO {}({}) VALUES ({})".format(
            table,
            ",".join(keys),
            ",".join(["?" for i in range(len(values))])
        )
        query = self.query(sql, tuple(values))
        return query.lastrowid
