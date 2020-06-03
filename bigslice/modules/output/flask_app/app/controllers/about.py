#!/usr/bin/env python3

import sqlite3
from flask import render_template

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('about', __name__)


@blueprint.route("/about")
def page_about():

    # todo: implements

    # page title
    page_title = "About BiG-SLiCE"
    page_subtitle = (
        "This software was initially developed and is currently"
        " maintained by Satria Kautsar (twitter:"
        " <a href='https://twitter.com/satriaphd'>@satriaphd</a>)"
        " as part of a fully funded PhD project granted to"
        " Dr. Marnix Medema (website: <a href='http://marnixmedema.nl'>"
        "marnixmedema.nl</a>, twitter: <a href='https://twitter.com/"
        "marnixmedema'>@marnixmedema</a>) by the <a href='"
        "https://www.graduateschool-eps.info/'>Graduate School of"
        " Experimental Plant Sciences</a>, NL. Contributions and feedbacks"
        " very welcomed. Feel free to <a href='mailto:satria.kautsar@wur.nl,"
        "marnix.medema@wur.nl?subject=[BiG-SLiCE contribution]'>drop us"
        " an e-mail</a> if you have any question regarding or related"
        " to BiG-SLiCE."
        "<br /> In the future, we aim to make BiG-SLiCE <strong>a"
        " comprehensive platform to do all sorts of downstream <u>large"
        " scale BGC analysis</u></strong>, taking advantage of its"
        " portable yet powerful SQLite3-based data storage combined with the"
        " flexible flask-based web app architecture as the foundation."
    )

    # render view
    return render_template(
        "about/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle
    )
