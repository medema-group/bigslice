#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigslice.modules.data.hmm

Handle registration of hmm tables and
performing hmmscan of aa sequences
"""

from os import path
from .database import Database
import glob
import json


class HMMDatabase:
    """Represents an hmm_db entry in the database"""

    def __init__(self, properties: dict):
        self.id = properties.get("id", -1)
        self.md5_biosyn_pfam = properties["md5_biosyn_pfam"]
        self.md5_sub_pfam = properties["md5_sub_pfam"]
        self.biosyn_pfams = properties["biosyn_pfams"]
        self.sub_pfams = properties["sub_pfams"]

    def save(self, database: Database):
        """commits hmm_db data"""

        existing = database.select(
            "hmm_db",
            "WHERE md5_biosyn_pfam=? AND md5_sub_pfam=?",
            parameters=(self.md5_biosyn_pfam, self.md5_sub_pfam)
        )
        if existing:
            # for now, this should not get called
            raise Exception("not_implemented")
            # current behavior: check if there is conflict
            # don't do anything if the same hmm_db exists
            assert len(existing) == 1
            existing = existing[0]
            if False:  # TODO: implements checking
                raise Exception("conflicting HMM_DB entry exists.")
            else:
                self.id = existing["id"]
                for biosyn_pfam in self.biosyn_pfams:
                    biosyn_pfam.id = int(database.select(
                        "hmm",
                        "WHERE name=? AND db_id=?",
                        parameters=(biosyn_pfam.name, self.id),
                        props=["id"]
                    )[0]["id"])
                for parent_acc in self.sub_pfams:
                    parent_id = int(database.select(
                        "hmm",
                        "WHERE accession=? AND db_id=?",
                        parameters=(parent_acc, self.id),
                        props=["id"]
                    )[0]["id"])
                    for sub_pfam in self.sub_pfams[parent_acc]:
                        sub_pfam.parent_id = parent_id
                        sub_pfam.id = int(database.select(
                            "hmm,subpfam",
                            "WHERE hmm.id=subpfam.hmm_id AND " +
                            "parent_hmm_id=? AND " +
                            "hmm.name=? AND hmm.db_id=?",
                            parameters=(parent_id, sub_pfam.name, self.id)
                        )[0]["id"])

        else:
            # insert new hmm_db
            self.id = database.insert(
                "hmm_db",
                {
                    "md5_biosyn_pfam": self.md5_biosyn_pfam,
                    "md5_sub_pfam": self.md5_sub_pfam
                }
            )
            # insert biosyn_pfam hmms
            pfam_ids = {}
            for biosyn_pfam in self.biosyn_pfams:
                biosyn_pfam.db_id = self.id
                biosyn_pfam.__save__(database)
                assert biosyn_pfam.id > -1
                pfam_ids[biosyn_pfam.accession] = biosyn_pfam.id
            # insert sub_pfam hmms
            for parent_acc in self.sub_pfams:
                parent_id = pfam_ids[parent_acc]
                for sub_pfam in self.sub_pfams[parent_acc]:
                    sub_pfam.db_id = self.id
                    sub_pfam.parent_id = parent_id
                    sub_pfam.__save__(database)

    @staticmethod
    def from_id(hmm_db_id: int, database: Database):
        """Load from hmm_db_id"""

        existing = database.select(
            "hmm_db",
            "WHERE id=?",
            parameters=(hmm_db_id,)
        )
        if existing:
            assert len(existing) == 1
            hmm_db = {
                "id": existing[0]["id"],
                "md5_biosyn_pfam": existing[0]["md5_biosyn_pfam"],
                "md5_sub_pfam": existing[0]["md5_sub_pfam"],
                "biosyn_pfams": [],
                "sub_pfams": {}
            }

            # fetch hmms
            parent_accessions = {}
            for hmm_row in database.select(
                "hmm",
                "LEFT JOIN subpfam" +
                " ON hmm.id=subpfam.hmm_id" +
                " WHERE db_id=?" +
                " ORDER BY parent_hmm_id ASC",
                parameters=(hmm_db_id,)
            ):
                hmm = {
                    "id": hmm_row["id"],
                    "db_id": hmm_db_id,
                    "name": hmm_row["name"],
                    "model_length": hmm_row["model_length"]
                }
                if not hmm_row["parent_hmm_id"]:
                    assert hmm_row["accession"]
                    parent_accessions[hmm["id"]] = hmm_row["accession"]
                    hmm["accession"] = hmm_row["accession"]
                    hmm_db["biosyn_pfams"].append(
                        HMMDatabase.HMM(hmm))
                else:
                    parent_accession = parent_accessions[
                        hmm_row["parent_hmm_id"]]
                    if parent_accession not in hmm_db["sub_pfams"]:
                        hmm_db["sub_pfams"][parent_accession] = []
                    hmm_db["sub_pfams"][parent_accession].append(
                        HMMDatabase.HMM(hmm))

            return HMMDatabase(hmm_db)

        return None

    @staticmethod
    def fetch_db_folder_info(db_folder_path: str):
        """Checks hmm models folder and match to the list of
        references in 'official_models.json'
        """

        # get md5sums values
        md5_biosyn_pfam = open(path.join(
            db_folder_path, "biosynthetic_pfams",
            "biopfam.md5sum"), "r").readline().rstrip()
        md5_sub_pfam = open(path.join(
            db_folder_path, "sub_pfams",
            "corepfam.md5sum"), "r").readline().rstrip()


        with open(path.join(path.dirname(path.abspath(__file__)),
            "official_models.json"), "r") as fstream:
            reference_dbs = json.load(fstream)
            for db_data in reference_dbs:
                if db_data["md5sums"] == [md5_biosyn_pfam, md5_sub_pfam]:
                    return db_data
            return None # using customized database


    @staticmethod
    def load_folder(db_folder_path: str, database: Database):
        """Loads a folder containing hmm models generated by
        generate_databases.py"""

        # get md5sums values and paths to hmm models
        md5_biosyn_pfam = open(path.join(
            db_folder_path, "biosynthetic_pfams",
            "biopfam.md5sum"), "r").readline().rstrip()
        md5_sub_pfam = open(path.join(
            db_folder_path, "sub_pfams",
            "corepfam.md5sum"), "r").readline().rstrip()

        existing = database.select(
            "hmm_db",
            "WHERE md5_biosyn_pfam=? AND md5_sub_pfam=?",
            parameters=(md5_biosyn_pfam, md5_sub_pfam),
            props=["id"]
        )

        if existing:
            # load from db
            assert len(existing) == 1
            result = HMMDatabase.from_id(existing[0]["id"], database)
        else:
            # create new hmm_db object
            biosyn_pfam_hmm = path.join(
                db_folder_path, "biosynthetic_pfams",
                "Pfam-A.biosynthetic.hmm")
            sub_pfam_hmms = glob.glob(path.join(
                db_folder_path, "sub_pfams", "hmm", "*.subpfams.hmm"))
            biosyn_pfams = HMMDatabase.HMM.from_file(biosyn_pfam_hmm)
            sub_pfams = {}
            for sub_pfam_hmm in sub_pfam_hmms:
                parent_acc = path.basename(
                    sub_pfam_hmm).split(".subpfams.hmm")[0]
                sub_pfams[parent_acc] = HMMDatabase.HMM.from_file(sub_pfam_hmm)

            result = HMMDatabase({
                "md5_biosyn_pfam": md5_biosyn_pfam,
                "md5_sub_pfam": md5_sub_pfam,
                "biosyn_pfams": biosyn_pfams,
                "sub_pfams": sub_pfams
            })

        return result

    class HMM:
        """Represents one hmm model
        Currently, hmm models are part of a hmm_db,
        meaning that a pfam accession will be considered
        different when linked to two separate hmm_dbs"""

        def __init__(self, properties: dict):
            self.id = properties.get("id", -1)
            self.parent_id = properties.get("parent_id", -1)
            self.db_id = properties.get("db_id", -1)
            self.accession = properties.get("accession", None)
            self.name = properties["name"]
            self.model_length = properties["model_length"]

        def __save__(self, database: Database):
            """commit hmm
            this only meant to be called from HMMDatabase.save()"""
            assert self.db_id > -1
            existing = database.select(
                "hmm",
                "WHERE name=? AND db_id=?",
                parameters=(self.name, self.db_id)
            )
            if existing:
                # for now, this should not get called
                raise Exception("not_implemented")
                # current behavior: check if there is conflict
                # don't do anything if the same entry exists
                assert len(existing) == 1
                existing = existing[0]
                if self.model_length != existing["model_length"]:
                    raise Exception("conflicting HMM entry for " +
                                    self.name)
                else:
                    self.id = existing["id"]
            else:
                # insert new hmm
                self.id = database.insert(
                    "hmm",
                    {
                        "db_id": self.db_id,
                        "name": self.name,
                        "accession": self.accession,
                        "model_length": self.model_length
                    }
                )
                if self.parent_id > -1:
                    # insert subpfam relationship
                    database.insert(
                        "subpfam",
                        {
                            "hmm_id": self.id,
                            "parent_hmm_id": self.parent_id
                        }
                    )

        @staticmethod
        def from_file(hmm_path: str):
            """Parse an hmm file, return all HMM objects"""

            results = []
            with open(hmm_path, "r") as hmm_file:
                properties = {}
                for line in hmm_file.readlines():
                    line = line.rstrip()
                    if line.startswith("NAME"):
                        properties["name"] = line.split(" ")[-1]
                    elif line.startswith("ACC"):
                        properties["accession"] = line.split(" ")[-1]
                    elif line.startswith("LENG"):
                        properties["model_length"] = int(
                            line.split(" ")[-1].rstrip())
                    elif line == "//":
                        results.append(HMMDatabase.HMM(properties))
                        properties = {}
                if properties != {}:
                    results.append(HMMDatabase.HMM(properties))
            return results
