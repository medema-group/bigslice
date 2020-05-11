#!/usr/bin/env python3
from flask import redirect

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('root', __name__)


@blueprint.route("/")
def page_root():
    return redirect("/summary")
