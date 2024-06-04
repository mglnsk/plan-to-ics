#!/usr/bin/env python3
from generator import GenerateIcal
import requests
from time import sleep

URL="https://wml.wat.edu.pl/wp-content/uploads/rozklady_zajec/2023_sem_lato/WMT23AX1S1.htm"

while True:
    try:
        resp = requests.get(URL, timeout=60)
        if resp.status_code != 200:
            print(f"invalid status?? code?? {resp.status_code}")
            sleep(60 * 30) # prevent rate limiting
            continue
        resp.encoding = 'windows-1250'
        body = resp.text

        output = GenerateIcal(body)
        with open("WMT23AX1S1.ics", "w") as f:
            f.write(output)
        
    except requests.exceptions.Timeout:
        print("got timedouted")
    sleep(60 * 15)