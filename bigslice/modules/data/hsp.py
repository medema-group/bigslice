#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigslice.modules.data.hsp

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
        self.parent_hsp_id = properties["parent_hsp_id"]
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
            if self.parent_hsp_id > 0:
                database.insert(
                    "hsp_subpfam",
                    {
                        "hsp_subpfam_id": self.id,
                        "hsp_parent_id": self.parent_hsp_id
                    }
                )
            if self.alignment:
                database.insert(
                    "hsp_alignment",
                    {
                        "hsp_id": self.id,
                        "model_start": self.alignment["model_start"],
                        "model_end": self.alignment["model_end"],
                        "model_gaps": ",".join(
                            map(str, self.alignment["model_gaps"])),
                        "cds_start": self.alignment["cds_start"],
                        "cds_end": self.alignment["cds_end"],
                        "cds_gaps": ",".join(
                            map(str, self.alignment["cds_gaps"]))
                    }
                )

    @staticmethod
    def parse_hmmtext(hmm_text_path: str,
                      hmm_ids: dict,
                      save_alignment: bool=True,
                      top_k: int=0,
                      rank_normalize: bool=False):
        """parse hmmtext result, create HSP object
        """

        if not path.exists(hmm_text_path):
            raise FileNotFoundError()

        results = []
        for run_result in parse(hmm_text_path, 'hmmer3-text'):
            # fetch query id
            try:
                # accession format: "bgc:X|cds:Y|start-end"
                bgc_id, cds_id, parent_hsp_id, locs = run_result.id.split("|")
                bgc_id = int(bgc_id.split("bgc:")[-1])
                cds_id = int(cds_id.split("cds:")[-1])
                parent_hsp_id = int(parent_hsp_id.split("hsp:")[-1])
                locs = tuple(map(int, locs.split("-")))
            except IndexError:
                raise Exception("couldn't parse {}".format(hmm_text_path))

            for idx, hsp in enumerate(run_result.hsps):

                # check top-k & if needs to be rank_normalized
                bitscore = hsp.bitscore
                if top_k > 0:
                    if idx >= top_k:
                        break
                    elif rank_normalize:
                        bitscore = 255 - int((255 / top_k) * idx)

                # fetch hmm id
                try:
                    hmm_id = hmm_ids[hsp.hit_id]
                except KeyError:
                    raise Exception(
                        "couldn't find hmm_id for {}".format(hsp.hit_id))

                # check if need to save alignment
                if save_alignment:
                    hsp_alignment = {
                        "model_start": hsp.hit_start,
                        "model_end": hsp.hit_end,
                        "model_gaps": [i for i, c
                                       in enumerate(str(hsp.hit.seq))
                                       if c == '.'],
                        "cds_start": hsp.query_start + locs[0],
                        "cds_end": hsp.query_end + locs[0],
                        "cds_gaps": [i for i, c
                                     in enumerate(str(hsp.query.seq))
                                     if c == '-']
                    }
                else:
                    hsp_alignment = None

                # save
                results.append(HSP({
                    "cds_id": cds_id,
                    "hmm_id": hmm_id,
                    "parent_hsp_id": parent_hsp_id,
                    "bitscore": bitscore,
                    "alignment": hsp_alignment
                }))

        return results
