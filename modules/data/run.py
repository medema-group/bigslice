#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.data.run

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
        self.time_start = properties["time_start"]
        self.time_end = properties.get("time_end", None)
        self.num_resumes = properties.get("num_resumes", 0)
        self.hmm_db_id = properties["hmm_db_id"]
        self.bgcs = properties["bgcs"]

    def save(self):
        """commits run data"""
        existing = self.database.select(
            "run",
            "WHERE prog_params=? AND time_start=?",
            parameters=(self.prog_params, self.time_start)
        )
        if existing:
            assert len(existing) == 1
            existing = existing[0]
            self.id = existing["id"]
        else:
            # insert new run
            assert self.status == 1
            assert self.num_resumes == 0
            self.id = self.database.insert(
                "run",
                {
                    "prog_params": self.prog_params,
                    "status": self.status,
                    "time_start": self.time_start,
                    "num_resumes": self.num_resumes,
                    "hmm_db_id": self.hmm_db_id
                }
            )
            # insert run_bgcs
            for bgc_id, status in self.bgcs:
                assert status == 1
                self.database.insert(
                    "run_bgc_status",
                    {
                        "run_id": self.id,
                        "bgc_id": bgc_id,
                        "status": status
                    }
                )

    @staticmethod
    def create(bgc_ids: Set[int], hmm_db_id: int, prog_params: str,
               run_start: datetime, database: Database,
               immediately_commits: bool=False):
        """Creates a new run object"""

        properties = {
            "status": 1,  # RUN_STARTED
            "time_start": run_start,
            "prog_params": prog_params,
            "hmm_db_id": hmm_db_id,
            "bgcs": [(bgc_id, 1) for bgc_id in bgc_ids]
        }

        run = Run(properties, database)

        if immediately_commits:
            run.save()

        return run

    @staticmethod
    def get_latest(hmm_db_id: int, database: Database):
        """fetch the last run in the database"""

        try:
            run_row = database.select(
                "run",
                "WHERE hmm_db_id=? ORDER BY id DESC",
                parameters=(hmm_db_id,)
            )[0]
            bgcs = [(bgc_row["bgc_id"], bgc_row["status"])
                    for bgc_row in database.select(
                "run_bgc_status",
                "WHERE run_id=? ORDER BY bgc_id ASC",
                parameters=(run_row["id"],)
            )]
            properties = {
                "id": run_row["id"],
                "prog_params": run_row["prog_params"],
                "status": run_row["status"],
                "time_start": run_row["time_start"],
                "time_end": run_row["time_end"],
                "num_resumes": run_row["num_resumes"],
                "hmm_db_id": run_row["hmm_db_id"],
                "bgcs": bgcs
            }
            return Run(properties, database)
        except ValueError:
            return None
