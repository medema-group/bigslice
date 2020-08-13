-- SQLite3 schema for the query results

-- query_schema ver.: 1.0.1, parent schema ver.: 1.0.1
CREATE TABLE IF NOT EXISTS schema (
    ver VARCHAR(10) PRIMARY KEY,
    parent_schema_ver VARCHAR(10)
);
INSERT OR IGNORE INTO schema VALUES('1.0.1', '1.0.1');

-- bgc
CREATE TABLE IF NOT EXISTS bgc (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(250) NOT NULL,
    type VARCHAR(10) NOT NULL, -- from source
    on_contig_edge BOOLEAN,
    length_nt INTEGER NOT NULL,
    orig_folder VARCHAR(1500) NOT NULL,
    orig_filename VARCHAR(1500) NOT NULL,
    UNIQUE(orig_folder, orig_filename)
);
CREATE INDEX IF NOT EXISTS bgc_name ON bgc(name);
CREATE INDEX IF NOT EXISTS bgc_type ON bgc(type);
CREATE INDEX IF NOT EXISTS bgc_gbkpath ON bgc(orig_folder, orig_filename);
CREATE INDEX IF NOT EXISTS bgc_filename ON bgc(orig_filename);
CREATE INDEX IF NOT EXISTS bgc_contigedge ON bgc(on_contig_edge);
CREATE INDEX IF NOT EXISTS bgc_length ON bgc(length_nt);

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

-- bgc_class
CREATE TABLE IF NOT EXISTS bgc_class (
    bgc_id INTEGER NOT NULL,
    chem_subclass_id INTEGER NOT NULL, -- from source
    FOREIGN KEY(bgc_id) REFERENCES bgc(id),
    FOREIGN KEY(chem_subclass_id) REFERENCES chem_subclass(id)
);
CREATE INDEX IF NOT EXISTS bgcclass_chemsubclass ON bgc_class(chem_subclass_id, bgc_id);
CREATE INDEX IF NOT EXISTS bgcclass_bgc ON bgc_class(bgc_id, chem_subclass_id);

-- hsp
CREATE TABLE IF NOT EXISTS hsp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cds_id INTEGER NOT NULL,
    hmm_id INTEGER NOT NULL, -- from source
    bitscore REAL NOT NULL,
    FOREIGN KEY(cds_id) REFERENCES cds(id)
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
CREATE INDEX IF NOT EXISTS hspalign_id ON hsp_alignment(hsp_id);
CREATE INDEX IF NOT EXISTS hspalign_model ON hsp_alignment(model_start);
CREATE INDEX IF NOT EXISTS hspalign_cds ON hsp_alignment(cds_start);

-- hsp_subpfam
CREATE TABLE IF NOT EXISTS hsp_subpfam (
    hsp_subpfam_id INTEGER NOT NULL,
    hsp_parent_id INTEGER NOT NULL,
    UNIQUE(hsp_subpfam_id, hsp_parent_id),
    FOREIGN KEY(hsp_subpfam_id) REFERENCES hsp(id),
    FOREIGN KEY(hsp_parent_id) REFERENCES hsp(id)
);
CREATE INDEX IF NOT EXISTS hspsubpfam_parent ON hsp_subpfam(hsp_parent_id, hsp_subpfam_id);
CREATE INDEX IF NOT EXISTS hspsubpfam_sub ON hsp_subpfam(hsp_subpfam_id, hsp_parent_id);

-- bgc_features
CREATE TABLE IF NOT EXISTS bgc_features (
    bgc_id INTEGER NOT NULL,
    hmm_id INTEGER NOT NULL, -- from source
    value INTEGER NOT NULL,
    UNIQUE(bgc_id, hmm_id),
    FOREIGN KEY(bgc_id) REFERENCES bgc(id)
);
CREATE INDEX IF NOT EXISTS bgc_features_bgc ON bgc_features(bgc_id, hmm_id, value);
CREATE INDEX IF NOT EXISTS bgc_features_bgc_value ON bgc_features(value, bgc_id, hmm_id);
CREATE INDEX IF NOT EXISTS bgc_features_hmm ON bgc_features(hmm_id, bgc_id, value);
CREATE INDEX IF NOT EXISTS bgc_features_hmm_value ON bgc_features(value, hmm_id, bgc_id);

-- gcf_membership
CREATE TABLE IF NOT EXISTS gcf_membership (
    gcf_id INTEGER NOT NULL,
    bgc_id INTEGER NOT NULL, -- from source
    membership_value INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    FOREIGN KEY(bgc_id) REFERENCES bgc(id)
);
CREATE INDEX IF NOT EXISTS gcf_membership_gcf_rank ON gcf_membership(gcf_id, rank);
CREATE INDEX IF NOT EXISTS gcf_membership_gcf_val ON gcf_membership(gcf_id, membership_value);
CREATE INDEX IF NOT EXISTS gcf_membership_bgc_rank ON gcf_membership(bgc_id, rank);
CREATE INDEX IF NOT EXISTS gcf_membership_bgc_val ON gcf_membership(bgc_id, membership_value);