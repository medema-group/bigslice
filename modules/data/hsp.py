#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.data.hsp

Handle registration of hmmscan results
"""

from os import path
from .database import Database
from Bio.SearchIO import parse


class HSP:
    """Represents a hsp entry in the database"""

    def __init__(self, properties: dict):
        self.id = properties.get("id", -1)
        self.cds_id = properties["cds_id"]
        self.hmm_id = properties["hmm_id"]
        self.bitscore = properties["bitscore"]
        self.alignment = properties.get("alignment", None)

    def save(self, database: Database):
        """commits hsp data"""
        if self.id > -1:
            raise Exception("not_implemented")
        else:
            self.id = database.insert(
                "hsp",
                {
                    "cds_id": self.cds_id,
                    "hmm_id": self.hmm_id,
                    "bitscore": self.bitscore
                }
            )
            if self.alignment:
                database.insert(
                    "hsp_alignment",
                    {                
                        "hsp_id": self.id,
                        "model_start": self.alignment["model_start"],
                        "model_end": self.alignment["model_end"],
                        "model_gaps": ",".join(map(str, self.alignment["model_gaps"])),
                        "cds_start": self.alignment["cds_start"],
                        "cds_end": self.alignment["cds_end"],
                        "cds_gaps": ",".join(map(str, self.alignment["cds_gaps"]))
                    }
                )

    @staticmethod
    def parse_hmmtext(hmm_text_path: str, hmm_ids: dict, save_alignment: bool=True):
        """parse hmmtext result, create HSP object
        """

        if not path.exists(hmm_text_path):
            raise FileNotFoundError()

        results = []

        for run_result in parse(hmm_text_path, 'hmmer3-text'):
            for hsp in run_result.hsps:

                try:
                    # accession format: "bgc:X|cds:Y"
                    bgc_id, cds_id = hsp.query_id.split("|")
                    bgc_id = int(bgc_id.split("bgc:")[-1])
                    cds_id = int(cds_id.split("cds:")[-1])
                except IndexError:
                    raise Exception("couldn't parse {}".format(hmm_text_path))

                try:
                    hmm_id = hmm_ids[hsp.hit_id]
                except KeyError:
                    raise Exception(
                        "couldn't find hmm_id for {}".format(hsp.hit_id))

                if save_alignment:
                    hsp_alignment = {
                        "model_start": hsp.hit_start,
                        "model_end": hsp.hit_end,
                        "model_gaps": [i for i, c
                                       in enumerate(str(hsp.hit.seq))
                                       if c == '.'],
                        "cds_start": hsp.query_start,
                        "cds_end": hsp.query_end,
                        "cds_gaps": [i for i, c
                                     in enumerate(str(hsp.query.seq))
                                     if c == '-']
                    }
                else:
                    hsp_alignment = None

                results.append(HSP({
                    "cds_id": cds_id,
                    "hmm_id": hmm_id,
                    "bitscore": hsp.bitscore,
                    "alignment": hsp_alignment                
                }))

        return results
