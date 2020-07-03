#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2020 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigslice.modules.data.taxonomy

Handle manipulation and storing of bgc taxonomy
"""

from .database import Database
from os import path


class Taxonomy:
    """Class handler for bgc taxonomy"""

    _CODE_KINGDOM = 0
    _CODE_PHYLUM = 1
    _CODE_CLASS = 2
    _CODE_ORDER = 3
    _CODE_FAMILY = 4
    _CODE_GENUS = 5
    _CODE_SPECIES = 6
    _CODE_ORGANISM = 7

    def __init__(self, properties: dict):
        self.dataset_id = properties["dataset_id"]
        self.path_startswith = properties["path_startswith"]
        self.taxonomy = {
            Taxonomy._CODE_KINGDOM: properties.get("Kingdom", ""),
            Taxonomy._CODE_PHYLUM: properties.get("Phylum", ""),
            Taxonomy._CODE_CLASS: properties.get("Class", ""),
            Taxonomy._CODE_ORDER: properties.get("Order", ""),
            Taxonomy._CODE_FAMILY: properties.get("Family", ""),
            Taxonomy._CODE_GENUS: properties.get("Genus", ""),
            Taxonomy._CODE_SPECIES: properties.get("Species", ""),
            Taxonomy._CODE_ORGANISM: properties.get("Organism", "")
        }

    def save(self, database: Database):
        """commits taxonomy data"""

        # add/query taxonomy entries
        tax_ids = []
        for level, name in self.taxonomy.items():
            if len(name) > 0:
                existing_taxa = database.select(
                    "taxon",
                    "WHERE level=? AND name LIKE ?",
                    parameters=(level, name),
                    props=["id"]
                )
                if len(existing_taxa) > 0:
                    tax_ids.append(existing_taxa[0]["id"])
                else:
                    # check inserts buffer
                    pending_ids = database.get_pending_id(
                        "taxon", {
                            "name": name,
                            "level": level
                        }
                    )
                    if len(pending_ids) > 0:
                        tax_ids.append(pending_ids[0])
                    else:
                        tax_ids.append(database.insert(
                            "taxon",
                            {
                                "level": level,
                                "name": name
                            }
                        ))

        # insert bgc_taxonomy
        bgc_ids = []
        for bgc in database.select(
            "bgc",
            "WHERE dataset_id={} AND orig_folder LIKE '{}' and orig_filename LIKE '{}%'".format(
                self.dataset_id,
                path.dirname(self.path_startswith),
                path.basename(self.path_startswith),
            ),
            props=["id"]
        ):
            bgc_ids.append(bgc["id"])
            for tax_id in tax_ids:
                database.insert(
                    "bgc_taxonomy",
                    {
                        "bgc_id": bgc["id"],
                        "taxon_id": tax_id
                    }
                )

        return bgc_ids
