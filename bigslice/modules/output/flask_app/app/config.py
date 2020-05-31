#!/usr/bin/env python3
from os import path

# path to result folder
conf = {
    "result_folder": path.join(path.dirname(__file__), "..", "result"),
    "reports_folder": path.join(path.dirname(__file__), "..", "reports")
}

conf["db_path"] = path.join(conf["result_folder"], "data.db")
conf["reports_db_path"] = path.join(conf["reports_folder"], "reports.db")
