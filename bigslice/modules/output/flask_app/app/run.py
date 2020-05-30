#!/usr/bin/env python3

from flask import Flask
from os import path
import sqlite3

# import global config
from .config import conf

# import controllers
from .controllers import root, summary, dataset, run
from .controllers import bgc, gcf
from .controllers import about, help_me, feedback
from .controllers.reports import main as reports


# initiate app
app = Flask(
    __name__,
    template_folder=path.join(path.dirname(path.realpath(__file__)), "views")
)

# register controllers
app.register_blueprint(root.blueprint)
app.register_blueprint(summary.blueprint)
app.register_blueprint(dataset.blueprint)
app.register_blueprint(bgc.blueprint)
app.register_blueprint(run.blueprint)
app.register_blueprint(gcf.blueprint)
app.register_blueprint(about.blueprint)
app.register_blueprint(help_me.blueprint)
app.register_blueprint(feedback.blueprint)
app.register_blueprint(reports.blueprint)

# app-specific contexts #


@app.context_processor
def inject_global():
    g = {
        "version": "1.0.0"
    }

    # for navigations
    nav_items = []
    nav_items.append(("Summary", "/summary"))

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # fetch dataset ids and names
        nav_items.append(("Datasets", [
            (ds_name, "/dataset/" + str(ds_id)) for
            ds_id, ds_name in cur.execute(
                "select id,name from dataset"
            ).fetchall()]
        ))
        nav_items[-1][1].insert(0, ("&lt;all&gt;", "/dataset/0"))

        # fetch run ids and names
        nav_items.append(("Runs", [
            ("run-{:04d}".format(run_id), "/run/" + str(run_id)) for
            run_id, in cur.execute(
                "select id from run order by id asc"
            ).fetchall()]
        ))

    nav_items.append(("Reports", [
        ("View all reports", "/reports/view"),
        ("Generate a new report", "/reports/new")
    ]))
    nav_items.append(("Help", "/help"))
    nav_items.append(("Feedback", "/feedback"))
    nav_items.append(("About", "/about"))

    return dict(
        g=g,
        nav_items=nav_items
    )
