#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigslice.modules.data.run

Handle manipulation and storage of run data
"""

from .database import Database
from typing import Set
from datetime import datetime


class Run:
    """Represents a run entry in the database"""

    def __init__(self, properties: dict, database: Database):
        self.id = properties.get("id", -1)
        self.database = database
        self.prog_params = properties["prog_params"]
        self.status = properties.get("status", 1)
        self.hmm_db_id = properties["hmm_db_id"]
        self.bgcs = properties["bgcs"]

    def save(self):
        """commits run data"""
        if self.id > -1:
            raise Exception("not_implemented")
        else:
            # insert new run
            assert self.status == 1
            self.id = self.database.insert(
                "run",
                {
                    "prog_params": self.prog_params,
                    "status": self.status,
                    "hmm_db_id": self.hmm_db_id
                }
            )
            # insert run_bgcs
            for bgc_id, status in self.bgcs.items():
                assert status == 1
                self.database.insert(
                    "run_bgc_status",
                    {
                        "run_id": self.id,
                        "bgc_id": bgc_id,
                        "status": status
                    }
                )

    def update_status(self, status: int):
        """update run status
        first check if all bgc_run_status
        has reached this point"""

        if self.id < 0:
            raise Exception("Run entry is not set")

        bgcs_not_processed = len(self.database.select(
            "run_bgc_status",
            "WHERE run_id=? AND status<?",
            parameters=(self.id, status)
        ))
        if bgcs_not_processed > 0:
            raise Exception("failed to update run status, " +
                            str(bgcs_not_processed) +
                            " BGCs are still unprocessed.")
        else:
            if self.database.update("run",
                                    {"status": status},
                                    "WHERE id=?",
                                    (self.id,)):
                self.status = status
                return 1
            else:
                return 0

    def log(self, message: str, commit_directly=True):
        """insert run_log entry"""

        if self.id < 0:
            raise Exception("Run entry is not set")

        self.database.insert(
            "run_log",
            {
                "run_id": self.id,
                "time_stamp": datetime.now(),
                "message": message
            }
        )
        if commit_directly:
            self.database.commit_inserts()

    @staticmethod
    def create(bgc_ids: Set[int], hmm_db_id: int,
               prog_params: str, database: Database):
        """Creates a new run object
        and immediately save it in the
        database"""

        properties = {
            "status": 1,  # RUN_STARTED
            "prog_params": prog_params,
            "hmm_db_id": hmm_db_id,
            "bgcs": {bgc_id: 1 for bgc_id in bgc_ids}
        }

        run = Run(properties, database)
        run.save()

        return run

    @staticmethod
    def fetch(run_id: int, database: Database):
        """fetch the specific run in the database"""

        try:
            run_row = database.select(
                "run",
                "WHERE id=?",
                parameters=(run_id,)
            )[0]
            bgcs = {bgc_row["bgc_id"]: bgc_row["status"]
                    for bgc_row in database.select(
                "run_bgc_status",
                "WHERE run_id=? ORDER BY bgc_id ASC",
                parameters=(run_row["id"],)
            )}
            properties = {
                "id": run_row["id"],
                "prog_params": run_row["prog_params"],
                "status": run_row["status"],
                "hmm_db_id": run_row["hmm_db_id"],
                "bgcs": bgcs
            }
            return Run(properties, database)
        except IndexError:
            return None

    @staticmethod
    def get_latest(hmm_db_id: int, database: Database,
                   min_status: int = 1):
        """fetch the last run in the database"""

        try:
            run_row = database.select(
                "run",
                "WHERE hmm_db_id=? AND status >= ?" +
                " ORDER BY id DESC",
                parameters=(hmm_db_id, min_status)
            )[0]
            bgcs = {bgc_row["bgc_id"]: bgc_row["status"]
                    for bgc_row in database.select(
                "run_bgc_status",
                "WHERE run_id=? ORDER BY bgc_id ASC",
                parameters=(run_row["id"],)
            )}
            properties = {
                "id": run_row["id"],
                "prog_params": run_row["prog_params"],
                "status": run_row["status"],
                "hmm_db_id": run_row["hmm_db_id"],
                "bgcs": bgcs
            }
            return Run(properties, database)
        except IndexError:
            return None
