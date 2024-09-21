#!/usr/bin/env bash
# arguments passed in $1 (url) and $2 (output file)
cd "$(dirname "$0")" || exit
source ./venv/bin/activate
python3 create_ics.py --link $1 --output $2
