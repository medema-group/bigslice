#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.data.bgc

Handle manipulation and storing of 'bgc' table
"""

from os import path
from Bio import SeqIO, SeqFeature
from .database import Database


class BGC:
    """Represents a BGC in the database"""

    def __init__(self, properties: dict, database: Database):
        self.database = database
        self.id = properties.get("id", -1)
        self.name = properties["name"]
        self.type = properties["type"]
        self.on_contig_edge = properties["on_contig_edge"]
        self.length_nt = properties["length_nt"]
        self.orig_filename = properties["orig_filename"]
        self.chem_subclasses = [BGC.ChemSubclass.search(
            self.database, cc, self.type)
            for cc in properties["chem_subclasses"]]
        self.taxons = properties["taxons"]
        self.cds = [BGC.CDS.from_feature(f)
                    for f in properties["cds_features"]]

    def save(self):
        """commits bgc data"""
        existing = self.database.select(
            "bgc",
            "WHERE name=?",
            parameters=(self.name,)
        ).fetchall()
        if existing:
            # current behavior: check if there is conflict
            # don't do anything if the same bgc exists
            assert len(existing) == 1
            existing = existing[0]
            if self.length_nt != existing["length_nt"]:
                raise Exception("conflicting BGC entry for " +
                                self.name)
            else:
                self.id = existing["id"]
        else:
            # insert new BGC
            self.id = self.database.insert(
                "bgc",
                {
                    "name": self.name,
                    "type": self.type,
                    "on_contig_edge": self.on_contig_edge,
                    "length_nt": self.length_nt,
                    "orig_filename": self.orig_filename
                }
            )
            # insert classes
            for chem_subclass in self.chem_subclasses:
                chem_subclass.bgc_id = self.id
                chem_subclass.__save__(self.database)
            # insert taxons
            for taxon in self.taxons:
                existing = self.database.select(
                    "taxon",
                    "WHERE name=?",
                    parameters=(taxon,)
                ).fetchall()
                if existing:
                    assert len(existing) == 1
                    taxon_id = existing[0]["id"]
                else:
                    taxon_id = self.database.insert(
                        "taxon", {"name": taxon}
                    )
                self.database.insert(
                    "bgc_taxonomy",
                    {
                        "bgc_id": self.id,
                        "taxon_id": taxon_id
                    }
                )
            # insert cds
            for cds in self.cds:
                cds.bgc_id = self.id
                cds.__save__(self.database)

    @staticmethod
    def parse_gbk(gbk_path: str, database: Database,
                  immediately_commits: bool=False):
        """Load BGCs from a gbk file, return a list of BGC
        objects (one gbk file can contain multiple BGCs e.g.
        in the case of antiSMASH5 GBKs"""

        orig_filename = path.basename(gbk_path)
        results = []

        gbk_type = None
        records = SeqIO.parse(gbk_path, "gb")
        for gbk in records:

            # fetch common stuff
            taxons = gbk.annotations["taxonomy"]

            # fetch type-specific information
            antismash_dict = gbk.annotations.get(
                "structured_comment", {}).get(
                "antiSMASH-Data", {})
            if antismash_dict.get("Version", "").startswith("5."):
                for feature in gbk.features:
                    if feature.type == "protocluster":
                        # is antiSMASH5 clustergbk
                        gbk_type = "as5"
                        break
                    elif feature.type == "subregion":
                        if "aStool" in feature.qualifiers and \
                                feature.qualifiers["aStool"][0] == "mibig":
                            gbk_type = "mibig"
                            break
                if not gbk_type:
                    print(orig_filename +
                          " is not a recognized antiSMASH clustergbk")
                    # not recognized, skip for now
                    pass

                elif gbk_type == "mibig":
                    for feature in gbk.features:
                        qual = feature.qualifiers
                        if feature.type == "subregion" and \
                            "aStool" in qual and \
                                qual["aStool"][0] == "mibig":
                            subreg = feature
                            name = gbk.id
                            on_edge = False
                            loc = subreg.location
                            len_nt = loc.end - loc.start
                            chem_subclasses = [label.strip() for label in
                                               qual["label"][0].split(",")]
                            cds_features = [f for f in
                                            gbk[loc.start:loc.end].features if
                                            f.type == "CDS"]
                            results.append(BGC({
                                "name": name,
                                "type": gbk_type,
                                "on_contig_edge": on_edge,
                                "length_nt": len_nt,
                                "orig_filename": orig_filename,
                                "chem_subclasses": chem_subclasses,
                                "taxons": taxons,
                                "cds_features": cds_features
                            }, database))

                elif gbk_type == "as5":
                    # get all candidate clusters that are
                    # single, interleaved, or chemical_hybrid
                    for feature in gbk.features:
                        qual = feature.qualifiers
                        if feature.type == "cand_cluster" and \
                                qual.get("kind", [""])[0] in \
                                ("single", "interleaved", "chemical_hybrid"):
                            cc = feature
                            name = path.splitext(orig_filename)[0] + \
                                ".cc" + \
                                qual["candidate_cluster_number"][0]
                            on_edge = qual["contig_edge"][0] == "True"
                            loc = cc.location
                            len_nt = loc.end - loc.start
                            chem_subclasses = qual["product"]
                            cds_features = [f for f in
                                            gbk[loc.start:loc.end].features if
                                            f.type == "CDS"]
                            results.append(BGC({
                                "name": name,
                                "type": gbk_type,
                                "on_contig_edge": on_edge,
                                "length_nt": len_nt,
                                "orig_filename": orig_filename,
                                "chem_subclasses": chem_subclasses,
                                "taxons": taxons,
                                "cds_features": cds_features
                            }, database))

            elif gbk.features[0].type == "cluster":
                # is antiSMASH4 clustergbk
                gbk_type = "as4"
                # TODO: implements antiSMASH4 parsing

            # for now, we only accepts as4, as5, mibig
            # (no multi records i.e. from mibig_old allowed)
            break

        if immediately_commits:
            # commit all new BGCs
            for bgc in results:
                bgc.save()

        return results

    class ChemSubclass:
        """Chemical subclass mapping"""

        def __init__(self, properties: dict):
            self.subclass_id = properties["subclass_id"]
            self.subclass_name = properties["subclass_name"]
            self.class_id = properties["class_id"]
            self.class_name = properties["class_name"]
            self.orig_class = properties["class_source"]

        def __save__(self, database: Database):
            """commit bgc_class
            this only meant to be called from BGC.save()"""
            existing = database.select(
                "bgc_class",
                "WHERE bgc_id=? AND chem_subclass_id=?",
                parameters=(self.bgc_id, self.subclass_id)
            ).fetchall()
            if existing:
                # current behavior: skip if exist
                assert len(existing) == 1
                pass
            else:
                # insert new map
                database.insert(
                    "bgc_class",
                    {
                        "bgc_id": self.bgc_id,
                        "chem_subclass_id": self.subclass_id
                    }
                )

        @staticmethod
        def search(database: Database, name: str, source_type: str):
            rows = database.select(
                "chem_class,chem_subclass,chem_subclass_map",
                "WHERE chem_subclass_map.subclass_id=chem_subclass.id AND " +
                "chem_class.id=chem_subclass.class_id " +
                "AND chem_subclass_map.type_source=? AND class_source=?",
                parameters=(source_type, name),
                props=["subclass_id", "class_id", "class_source",
                       "chem_class.name as class_name",
                       "chem_subclass.name as subclass_name"]
            ).fetchall()
            assert len(rows) == 1
            row = rows[0]
            return BGC.ChemSubclass(row)

    class CDS:
        """Represents a CDS in the database
        CDS can't exists without a BGC"""

        def __init__(self, properties: dict):
            self.id = properties.get("id", -1)
            self.nt_start = properties["nt_start"]
            self.nt_end = properties["nt_end"]
            self.strand = properties["strand"]
            self.locus_tag = properties["locus_tag"]
            self.protein_id = properties["protein_id"]
            self.product = properties["product"]
            self.aa_seq = properties["aa_seq"]

        def __save__(self, database: Database):
            """commit cds
            this only meant to be called from BGC.save()"""
            existing = database.select(
                "cds",
                "WHERE bgc_id=? AND locus_tag=?",
                parameters=(self.bgc_id, self.locus_tag)
            ).fetchall()
            if existing:
                # current behavior: check if there is conflict
                # don't do anything if the same cds exists
                assert len(existing) == 1
                existing = existing[0]
                if self.aa_seq != existing["aa_seq"]:
                    raise Exception("conflicting CDS entry for " +
                                    self.locus_tag)
                else:
                    self.id = existing["id"]
            else:
                # insert new CDS
                self.id = database.insert(
                    "cds",
                    {
                        "bgc_id": self.bgc_id,
                        "nt_start": self.nt_start,
                        "nt_end": self.nt_end,
                        "strand": self.strand,
                        "locus_tag": self.locus_tag,
                        "protein_id": self.protein_id,
                        "product": self.product,
                        "aa_seq": self.aa_seq
                    }
                )

        @staticmethod
        def from_feature(feature: SeqFeature):
            def get_prop(prop):
                return feature.qualifiers.get(prop, [None])[0]
            loc = feature.location
            properties = {
                "nt_start": loc.start,
                "nt_end": loc.end,
                "strand": feature.strand,
                "locus_tag": get_prop("locus_tag"),
                "protein_id": get_prop("protein_id"),
                "product": get_prop("product"),
                "aa_seq": get_prop("translation")
            }
            return BGC.CDS(properties)
