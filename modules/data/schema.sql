-- SQLite3 schema for storage and manipulation of BiGSSCUIT data

-- schema ver.: 1.0.0
CREATE TABLE IF NOT EXISTS schema (
    ver VARCHAR(10) PRIMARY KEY
);
INSERT OR IGNORE INTO schema VALUES('1.0.0');

-- bgc
CREATE TABLE IF NOT EXISTS bgc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(250) NOT NULL UNIQUE,
    type VARCHAR(10) NOT NULL,
    on_contig_edge BOOLEAN,
    length_nt INTEGER NOT NULL,
    orig_filename VARCHAR(250),
    FOREIGN KEY(type) REFERENCES enum_bgc_type(code)
);

-- enum_bgc_type
CREATE TABLE IF NOT EXISTS enum_bgc_type (
    code VARCHAR(10) PRIMARY KEY,
    description VARCHAR(250)
);
INSERT OR IGNORE INTO enum_bgc_type VALUES ('as4', 'antiSMASH4 clusterXXX.gbk');
INSERT OR IGNORE INTO enum_bgc_type VALUES ('as5', 'antiSMASH5 regionXXX.gbk');
INSERT OR IGNORE INTO enum_bgc_type VALUES ('mibig', 'MIBiG >= 2.0 gbk');

-- cds
CREATE TABLE IF NOT EXISTS cds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bgc_id INTEGER NOT NULL,
    nt_start INTEGER NOT NULL,
    nt_end INTEGER NOT NULL,
    strand INTEGER CHECK(strand IN (-1,0,1)),
    locus_tag VARCHAR(100) NOT NULL,
    protein_id VARCHAR(100),
    product VARCHAR(100),
    aa_seq TEXT NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id)
);

-- hmm_db
CREATE TABLE IF NOT EXISTS hmm_db (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    md5_biosyn_pfam CHAR(32) NOT NULL,
    md5_sub_pfam CHAR(32) NOT NULL
);

-- hmm
CREATE TABLE IF NOT EXISTS hmm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    accession VARCHAR(10) NOT NULL,
    name VARCHAR(25) NOT NULL,
    db_id INTEGER NOT NULL,
    model_length INTEGER NOT NULL,
    FOREIGN KEY(db_id) REFERENCES hmm_db(id)
);

-- hsp
CREATE TABLE IF NOT EXISTS hsp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cds_id INTEGER NOT NULL,
    hmm_id INTEGER NOT NULL,
    bitscore DECIMAL(38,2) NOT NULL,
    model_start INTEGER NOT NULL,
    model_end INTEGER NOT NULL,
    model_gaps TEXT NOT NULL,
    cds_start INTEGER NOT NULL,
    cds_end INTEGER NOT NULL,
    cds_gaps TEXT NOT NULL,
    FOREIGN KEY(cds_id) REFERENCES cds(id),
    FOREIGN KEY(hmm_id) REFERENCES hmm(id)    
);

-- taxon
CREATE TABLE IF NOT EXISTS taxon (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

-- bgc_taxonomy
CREATE TABLE IF NOT EXISTS bgc_taxonomy (
    bgc_id INTEGER NOT NULL,
    taxon_id INTEGER NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id),
    FOREIGN KEY(taxon_id) REFERENCES taxon(id)
);

-- chem_class
CREATE TABLE IF NOT EXISTS chem_class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Alkaloid');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'NRP');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Other');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Polyketide');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'RiPP');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Saccharide');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Terpene');

-- chem_subclass
CREATE TABLE IF NOT EXISTS chem_subclass (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY(class_id) REFERENCES chem_class(id)
);

-- chem_subclass_map
CREATE TABLE IF NOT EXISTS chem_subclass_map (
    class_source VARCHAR(100) NOT NULL,
    type_source VARCHAR(10) NOT NULL,    
    subclass_id INTEGER NOT NULL,
    FOREIGN KEY(type_source) REFERENCES enum_bgc_type(code),
    FOREIGN KEY(subclass_id) REFERENCES chem_subclass(id)
);

-- bgc_class
CREATE TABLE IF NOT EXISTS bgc_class (
    bgc_id INTEGER NOT NULL,
    chem_subclass_id INTEGER NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id),
    FOREIGN KEY(chem_subclass_id) REFERENCES chem_subclass(id)
);

-- enum_run_status
CREATE TABLE IF NOT EXISTS enum_run_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);
INSERT OR IGNORE INTO enum_run_status VALUES (1, 'RUN_STARTED');
INSERT OR IGNORE INTO enum_run_status VALUES (1, 'INPUT_STORED');
INSERT OR IGNORE INTO enum_run_status VALUES (1, 'BIOSYN_SCANNED');
INSERT OR IGNORE INTO enum_run_status VALUES (1, 'SUBPFAM_SCANNED');
INSERT OR IGNORE INTO enum_run_status VALUES (1, 'FEATURES_EXTRACTED');
INSERT OR IGNORE INTO enum_run_status VALUES (1, 'CLUSTERING_FINISHED');
INSERT OR IGNORE INTO enum_run_status VALUES (1, 'RUN_FINISHED');

-- run
CREATE TABLE IF NOT EXISTS run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status INTEGER NOT NULL,
    prog_params VARCHAR(250) NOT NULL,
    time_start DATETIME NOT NULL,
    time_end DATETIME,
    is_disrupted BOOLEAN,
    hmm_db_id INTEGER,
    FOREIGN KEY(status) REFERENCES enum_run_status(id),
    FOREIGN KEY(hmm_db_id) REFERENCES hmm_db(id)
);

-- run_bgc_status
CREATE TABLE IF NOT EXISTS run_bgc_status (
    bgc_id INTEGER NOT NULL,
    run_id INTEGER NOT NULL,
    status INTEGER NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id),
    FOREIGN KEY(run_id) REFERENCES run(id),
    FOREIGN KEY(status) REFERENCES enum_run_status(id)
);

-- gcf
CREATE TABLE IF NOT EXISTS gcf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    centroid TEXT NOT NULL,
    FOREIGN KEY(run_id) REFERENCES run(id)
);

-- gcf_membership
CREATE TABLE IF NOT EXISTS gcf_membership (
    gcf_id INTEGER NOT NULL,
    bgc_id INTEGER NOT NULL,
    membership_value DECIMAL(5, 2) NOT NULL,
    FOREIGN KEY(gcf_id) REFERENCES gcf(id),
    FOREIGN KEY(bgc_id) REFERENCES bgc(id)
);

-- feature
CREATE TABLE IF NOT EXISTS feature (
    bgc_id INTEGER NOT NULL,
    feature TEXT NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id)
);