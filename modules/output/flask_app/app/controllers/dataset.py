#!/usr/bin/env python3

import sqlite3
from flask import render_template

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('dataset', __name__)


@blueprint.route("/dataset/<int:dataset_id>")
def page_dataset(dataset_id):

    # todo: implements

    # page title
    page_title = "Dataset"
    page_subtitle = (
        "under construction"
    )

    # render view
    return render_template(
        "dataset/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle
    )
