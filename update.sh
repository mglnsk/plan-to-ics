#!/usr/bin/env bash
cd "$(dirname "$0")" || exit
source ./venv/bin/activate
mkdir -p calendars

while read -r line
do
    sleep $((RANDOM % 2))
    python3 ./create_ics.py --id "${line}" --output "./calendars/${line}.ics"
    sleep $((RANDOM % 8))
done < list.txt

rsync -a calendars/ ~/wat/static/calendars/
rsync -a calendars/ /var/www/wat/calendars/
