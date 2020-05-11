#!/usr/bin/bash

DIR="$(dirname "$(readlink -f "$0")")"
export FLASK_APP="$DIR/app/run.py"

# run flask server
flask run