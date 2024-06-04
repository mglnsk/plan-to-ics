#!/usr/bin/env python3

import requests
import argparse
from parser import generate_ical

def get_html(url: str) -> str:
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            print(f"invalid status?? code?? {resp.status_code}")
            exit(1)
        resp.encoding = 'windows-1250'
        body = resp.text
        return body
        
    except requests.exceptions.Timeout:
        print("got timedouted")
        exit(1)


parser = argparse.ArgumentParser(description='Convert plansoft link to a calendar file')
parser.add_argument("--link", type=str, help="direct link to the html file", default="https://wml.wat.edu.pl/wp-content/uploads/rozklady_zajec/2023_sem_lato/WMT23AX1S1.htm")
parser.add_argument("--output", type=str, help="output file. preferably ending with .ics", default="calendar.ics")

args = parser.parse_args()


plan = get_html(args.link)
ical = generate_ical(plan)

with open(args.output, encoding="utf-8", mode="w") as f:
    f.write(ical)