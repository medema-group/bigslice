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
        " <strong><a href='#help_faq'>Frequently Asked Questions</a></strong>"
        " to see if your question is already answered there."
        " <!--Additionally, check out the <strong>"
        "<a href='#help_howitworks'>How it works</a></strong> section"
        " to understand the underlying algorithm and concept that"
        " BiG-SLiCE uses.-->"
    )

    # FAQs
    faqs = [
        (
            "Please help us!",
            (
                "We're collecting questions from users to put in this FAQ"
                " section. Feel free to send yours to our e-mail (see above)."
            )
        )
    ]

    # render view
    return render_template(
        "help/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle,
        faqs=faqs
    )
