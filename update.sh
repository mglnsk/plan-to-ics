#!/usr/bin/env bash
cd "$(dirname "$0")" || exit
source ./venv/bin/activate

mkdir -p calendars

cat list.txt | while read line
do
    sleep $((RANDOM % 2))
    #./create_ics.sh "https://wml.wat.edu.pl/wp-content/uploads/rozklady_zajec/2023_sem_lato/${line}.htm" "./calendars/${line}.ics"
    python3 ./create_ics.py --id "${line}" --output "./calendars/${line}.ics"
    sleep $((RANDOM % 8))
done

rsync -a calendars/ /var/www/wat/calendars/
