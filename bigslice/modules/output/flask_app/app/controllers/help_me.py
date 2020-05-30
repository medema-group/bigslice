#!/usr/bin/env python3

import sqlite3
from flask import render_template

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('help_me', __name__)


@blueprint.route("/help")
def page_help():

    # todo: implements

    # page title
    page_title = "Help"
    page_subtitle = (
        "Got a question regarding or related to BiG-SLiCE?"
        " feel free to <a href='mailto:satria.kautsar@wur.nl,"
        "marnix.medema@wur.nl?subject=[BiG-SLiCE HELP]"
        " ...&body=Dear BiG-SLiCE developers, ...'>"
        "drop us an e-mail</a> (please put <strong>"
        "[BiG-SLiCE HELP]</strong> on the subject)."
        " Be sure to first check these"
        " <strong>Frequently Asked Questions</strong>"
        " to see if your question is already answered there."
    )

    # FAQs
    faqs = [
        (
            "dummy-question#1?",
            "dummy-answer#1"
        ),
        (
            "dummy-question#2?",
            "dummy-answer#2"
        ),
        (
            "dummy-question#3?",
            "dummy-answer#3"
        )
    ]

    # render view
    return render_template(
        "help/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle,
        faqs=faqs
    )
