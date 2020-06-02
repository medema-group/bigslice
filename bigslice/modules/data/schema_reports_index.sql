-- sqlite3 database to store all generated reports (including queries)
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type VARCHAR(250) NOT NULL,
    name VARCHAR(250) NOT NULL,
    creation_date DATETIME NOT NULL,
    UNIQUE(type, name)
);
CREATE INDEX IF NOT EXISTS reports_type_name ON reports(type, name);
CREATE INDEX IF NOT EXISTS reports_type_date ON reports(type, creation_date);
CREATE INDEX IF NOT EXISTS reports_date ON reports(creation_date);
CREATE INDEX IF NOT EXISTS reports_name ON reports(name);

CREATE TABLE IF NOT EXISTS reports_run (
    report_id INTEGER NOT NULL,
    run_id INTEGER NOT NULL,
    UNIQUE(report_id, run_id)
);
CREATE INDEX IF NOT EXISTS reports_run_report ON reports_run(report_id, run_id);
CREATE INDEX IF NOT EXISTS reports_run_run ON reports_run(run_id, report_id);