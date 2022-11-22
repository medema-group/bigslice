#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
"""
config file for generate_databases.py
"""

db_config = {}

# database URLs
db_config["PFAM_DB_URL"] = "https://ftp.ebi.ac.uk/pub/databases/Pfam/releases/Pfam35.0/Pfam-A.hmm.gz"
db_config["ANTISMASH_URL"] = "https://github.com/antismash/antismash/archive/refs/heads/master.zip"
db_config["ANTISMASH_VERSION"] = "antismash-rc-ab8fb9220474e824f938676a638545f9d7b2e084"
db_config["REFERENCE_PROTEINS_URL"] = "https://proteininformationresource.org/rps/data/2022_04/15/rp-seqs-15.fasta.gz"

# build_subpfam algorithm parameters
db_config["MIN_CLADE_NUMBERS"] = 3
db_config["MAX_CLADE_NUMBERS"] = 50
db_config["MIN_PROTEIN_SEQUENCES"] = 5
