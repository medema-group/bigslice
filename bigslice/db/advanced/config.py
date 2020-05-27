#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""
config file for generate_databases.py
"""

db_config = {}

# database URLs
db_config["PFAM_DB_URL"] = "ftp://ftp.ebi.ac.uk/pub/" + \
    "databases/Pfam/releases/Pfam31.0/Pfam-A.hmm.gz"
db_config["ANTISMASH_URL"] = "https://github.com/" + \
    "antismash/antismash/archive/5-1-1.tar.gz"
db_config["ANTISMASH_VERSION"] = "antismash-5-1-1"
db_config["REFERENCE_PROTEINS_URL"] = "ftp://ftp.pir.georgetown.edu/" + \
    "databases/rps/rp-seqs-15.fasta.gz"

# build_subpfam algorithm parameters
db_config["MIN_CLADE_NUMBERS"] = 3
db_config["MAX_CLADE_NUMBERS"] = 50
db_config["MIN_PROTEIN_SEQUENCES"] = 5
