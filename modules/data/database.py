#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.data.database

Common classes and functions to work with the SQLite3 database
"""

from os import path
import re
import sqlite3
from threading import Lock


class Database:
    """Wrapper class to do manipulation on an SQLite3 database file"""

    def __init__(self, db_path: str):
        """db_path: path to sqlite3 database file"""

        self._db_path = db_path
        self._insert_queues = []
        self._last_indexes = {}

        # get schema information
        sql_schema = open(path.join(path.dirname(
            path.abspath(__file__)), "schema.sql"), "r").read()
        self.schema_ver = re.search(
            r"\n-- schema ver\.: (?P<ver>1\.0\.0)", sql_schema).group("ver")

        if path.exists(self._db_path):
            # check if existing one have the same schema version
            db_schema_ver = self.select("schema", "WHERE 1")[0]["ver"]
            if db_schema_ver != self.schema_ver:
                raise Exception(
                    "SQLite3 database exists but contains different schema " +
                    "version ({} rather than {}), exiting!".format(
                        db_schema_ver, self.schema_ver))
            else:
                # fetch last_indexes from db
                for row in self.select("sqlite_sequence", "WHERE 1"):
                    self._last_indexes[row["name"]] = row["seq"]
        else:
            # create new database
            with sqlite3.connect(self._db_path) as db_con:
                db_cur = db_con.cursor()
                db_cur.executescript(sql_schema)
                # load bs_class rows into a dictionary for quick searching
                bs_classes_id = {}
                for row in self.select(
                    "chem_class",
                    "WHERE 1"
                ):
                    bs_classes_id[row["name"]] = row["id"]
                # load chem_class_map.tsv
                with open(path.join(path.dirname(path.abspath(__file__)),
                                    "chem_class_map.tsv"), "r") as tsv:
                    tsv.readline()  # skip header
                    for line in tsv:
                        src_class, src, bs_class, bs_subclass = \
                            line.rstrip().split("\t")
                        if bs_subclass == "":  # TODO: enforce strict
                            bs_subclass = "other"
                        if bs_class == "":  # TODO: enforce strict
                            bs_class = "Other"
                        bs_class_id = bs_classes_id[bs_class]

                        existing = self.select(
                            "chem_subclass",
                            "WHERE name=? AND class_id=?",
                            parameters=(bs_subclass, bs_class_id)
                        )
                        if existing:
                            assert len(existing) == 1
                            bs_subclass_id = existing[0]["id"]
                        else:
                            bs_subclass_id = self.insert(
                                "chem_subclass",
                                {
                                    "name": bs_subclass,
                                    "class_id": bs_class_id
                                }
                            )

                        self.insert("chem_subclass_map", {
                            "class_source": src_class,
                            "type_source": src,
                            "subclass_id": bs_subclass_id
                        })

    def select(self, table: str, clause: str,
               parameters: tuple = None, props: list = []):
        """execute a SELECT ... FROM ... WHERE"""

        def dict_factory(cursor, row):
            """see https://docs.python.org/2/library/
            sqlite3.html#sqlite3.Connection.row_factory"""
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        if len(props) < 1:
            props_string = "*"
        else:
            props_string = ",".join(props)

        sql = "SELECT {} FROM {} {}".format(
            props_string,
            table,
            clause
        )

        with sqlite3.connect(self._db_path) as db_con:
            db_con.row_factory = dict_factory
            db_cur = db_con.cursor()
            if parameters:
                return db_cur.execute(sql, parameters).fetchall()
            else:
                return db_cur.execute(sql).fetchall()

    def insert(self, table: str, data: dict):
        """execute an INSERT INTO ... VALUES ...
        !!don't use the returned IDs unless you are sure
        that the INSERTs all will be successful!!"""

        keys = []
        values = []
        for key, value in data.items():
            if key == "id":  # can't have this around!
                raise Exception("Don't specify id for INSERTs!")
            keys.append(key)
            values.append(value)

        sql = "INSERT INTO {}({}) VALUES ({})".format(
            table,
            ",".join(keys),
            ",".join(["?" for i in range(len(values))])
        )

        with Lock() as lock:  # this needs to be thread-safe
            with sqlite3.connect(self._db_path) as db_con:
                db_cur = db_con.cursor()
                return db_cur.execute(sql, tuple(values)).lastrowid
