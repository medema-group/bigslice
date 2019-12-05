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
    orig_filename VARCHAR(250) NOT NULL,
    FOREIGN KEY(type) REFERENCES enum_bgc_type(code)
);
CREATE INDEX IF NOT EXISTS bgc_type ON bgc(type);
CREATE INDEX IF NOT EXISTS bgc_filename ON bgc(orig_filename);
CREATE INDEX IF NOT EXISTS bgc_contigedge ON bgc(on_contig_edge);
CREATE INDEX IF NOT EXISTS bgc_length ON bgc(length_nt);

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
    locus_tag VARCHAR(100),
    protein_id VARCHAR(100),
    product VARCHAR(100),
    aa_seq TEXT NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id)
);
CREATE INDEX IF NOT EXISTS cds_bgc ON cds(bgc_id,nt_start,nt_end);

-- hmm_db
CREATE TABLE IF NOT EXISTS hmm_db (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    md5_biosyn_pfam CHAR(32) NOT NULL,
    md5_sub_pfam CHAR(32) NOT NULL
);

-- hmm
CREATE TABLE IF NOT EXISTS hmm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    accession VARCHAR(10),
    name VARCHAR(25) NOT NULL,
    db_id INTEGER NOT NULL,
    model_length INTEGER NOT NULL,
    FOREIGN KEY(db_id) REFERENCES hmm_db(id)
);
CREATE INDEX IF NOT EXISTS hmm_acc ON hmm(db_id, accession);
CREATE INDEX IF NOT EXISTS hmm_name ON hmm(db_id, name);

-- subpfam
CREATE TABLE IF NOT EXISTS subpfam (
    hmm_id INTEGER NOT NULL,
    parent_hmm_id INTEGER NOT NULL,
    FOREIGN KEY(hmm_id) REFERENCES hmm(id),
    FOREIGN KEY(parent_hmm_id) REFERENCES hmm(id)
);
CREATE INDEX IF NOT EXISTS subpfam_parenthmm ON subpfam(parent_hmm_id, hmm_id);

-- hsp
CREATE TABLE IF NOT EXISTS hsp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cds_id INTEGER NOT NULL,
    hmm_id INTEGER NOT NULL,
    bitscore DECIMAL(4,2) NOT NULL,
    FOREIGN KEY(cds_id) REFERENCES cds(id),
    FOREIGN KEY(hmm_id) REFERENCES hmm(id)    
);
CREATE INDEX IF NOT EXISTS hsp_cdshmm ON hsp(cds_id, hmm_id);
CREATE INDEX IF NOT EXISTS hsp_bitscore ON hsp(bitscore);

-- hsp_alignment
CREATE TABLE IF NOT EXISTS hsp_alignment (
    hsp_id INTEGER UNIQUE NOT NULL,
    model_start INTEGER NOT NULL,
    model_end INTEGER NOT NULL,
    model_gaps TEXT NOT NULL,
    cds_start INTEGER NOT NULL,
    cds_end INTEGER NOT NULL,
    cds_gaps TEXT NOT NULL,
    FOREIGN KEY(hsp_id) REFERENCES hsp(id)
);

-- taxon
CREATE TABLE IF NOT EXISTS taxon (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);
CREATE UNIQUE INDEX IF NOT EXISTS taxon_name ON taxon(name);

-- bgc_taxonomy
CREATE TABLE IF NOT EXISTS bgc_taxonomy (
    bgc_id INTEGER NOT NULL,
    taxon_id INTEGER NOT NULL,
    level INTEGER NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id),
    FOREIGN KEY(taxon_id) REFERENCES taxon(id)
);
CREATE INDEX IF NOT EXISTS bgctaxonomy_bgcid ON bgc_taxonomy(bgc_id, level);
CREATE INDEX IF NOT EXISTS bgctaxonomy_level ON bgc_taxonomy(level);

-- chem_class
CREATE TABLE IF NOT EXISTS chem_class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Unknown');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Other');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Alkaloid');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'NRP');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Polyketide');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'RiPP');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Saccharide');
INSERT OR IGNORE INTO chem_class VALUES (NULL, 'Terpene');
CREATE UNIQUE INDEX IF NOT EXISTS chemclass_name ON chem_class(name);

-- chem_subclass
CREATE TABLE IF NOT EXISTS chem_subclass (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    FOREIGN KEY(class_id) REFERENCES chem_class(id)
);
CREATE INDEX IF NOT EXISTS chemsubclass_name ON chem_subclass(name);
CREATE INDEX IF NOT EXISTS chemsubclass_class ON chem_subclass(class_id, name);


-- chem_subclass_map
CREATE TABLE IF NOT EXISTS chem_subclass_map (
    class_source VARCHAR(100) NOT NULL,
    type_source VARCHAR(10) NOT NULL,    
    subclass_id INTEGER NOT NULL,
    FOREIGN KEY(type_source) REFERENCES enum_bgc_type(code),
    FOREIGN KEY(subclass_id) REFERENCES chem_subclass(id)
);
CREATE INDEX IF NOT EXISTS chemsubclassmap_source ON chem_subclass_map(type_source, class_source);

-- bgc_class
CREATE TABLE IF NOT EXISTS bgc_class (
    bgc_id INTEGER NOT NULL,
    chem_subclass_id INTEGER NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id),
    FOREIGN KEY(chem_subclass_id) REFERENCES chem_subclass(id)
);
CREATE INDEX IF NOT EXISTS bgcclass_chemsubclass ON bgc_class(chem_subclass_id);

-- enum_run_status
CREATE TABLE IF NOT EXISTS enum_run_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);
INSERT OR IGNORE INTO enum_run_status VALUES (1, 'RUN_STARTED');
INSERT OR IGNORE INTO enum_run_status VALUES (2, 'BIOSYN_SCANNED');
INSERT OR IGNORE INTO enum_run_status VALUES (3, 'SUBPFAM_SCANNED');
INSERT OR IGNORE INTO enum_run_status VALUES (4, 'FEATURES_EXTRACTED');
INSERT OR IGNORE INTO enum_run_status VALUES (5, 'CLUSTERING_FINISHED');
INSERT OR IGNORE INTO enum_run_status VALUES (6, 'RUN_FINISHED');
CREATE UNIQUE INDEX IF NOT EXISTS enumrunstatus_name ON enum_run_status(name);

-- run
CREATE TABLE IF NOT EXISTS run (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status INTEGER NOT NULL,
    prog_params VARCHAR(250) NOT NULL,
    time_start DATETIME NOT NULL,
    time_end DATETIME,
    num_resumes INTEGER DEFAULT 0,
    hmm_db_id INTEGER,
    FOREIGN KEY(status) REFERENCES enum_run_status(id),
    FOREIGN KEY(hmm_db_id) REFERENCES hmm_db(id)
);
CREATE INDEX IF NOT EXISTS run_hmmdb ON run(hmm_db_id, status, time_start);

-- run_bgc_status
CREATE TABLE IF NOT EXISTS run_bgc_status (
    bgc_id INTEGER NOT NULL,
    run_id INTEGER NOT NULL,
    status INTEGER NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id),
    FOREIGN KEY(run_id) REFERENCES run(id),
    FOREIGN KEY(status) REFERENCES enum_run_status(id)
);
CREATE INDEX IF NOT EXISTS runbgcstatus_run ON run_bgc_status(run_id, status);

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
    run_id INTEGER NOT NULL,
    feature TEXT NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id),
    FOREIGN KEY(run_id) REFERENCES run(id)
);