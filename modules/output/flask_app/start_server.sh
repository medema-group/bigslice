#!/usr/bin/bash

DIR="$(dirname "$(readlink -f "$0")")"
export FLASK_APP="$DIR/app/run.py"

# run flask server
if [ -z "$1" ]
then
  port="5000"
else
  port=$1
fi
flask run --host=0.0.0.0 --port=$port