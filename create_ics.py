#!/usr/bin/env python3
import requests
import argparse
from parser import generate_ical
from bs4 import BeautifulSoup
import re
from datetime import date, datetime
from ical.calendar import Calendar
from ical.event import Event
from ical.calendar_stream import IcsCalendarStream

DAYS=["pon.", "wt.", "śr.", "czw.", "pt.", "sob.", "niedz."]
ROMAN_TO_MONTH = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
HOUR_TRANSLATION = {
    " 1-2": ("8:00", "9:35"),
    " 3-4": ("9:50", "11:25"),
    " 5-6": ("11:40", "13:15"),
    " 7-8": ("13:30", "15:05"),
    " 9-10": ("15:45", "17:20"),
    " 11-12": ("17:35", "19:10"),
    " 13-14": ("19:25", "21:00")
}

def create_calendar(hours: dict, days: dict) -> str:
    calendar = Calendar()
    for day_name in hours:
        for hour_block in hours[day_name]:
            for h_pos, event in enumerate(hours[day_name][hour_block]):
                day_month = days[day_name][h_pos]
                (day_of_the_month, month_number_roman) = day_month.split(" ")
                month_number = ROMAN_TO_MONTH.index(month_number_roman) + 1
                summary = event[0]
                (start_hour, end_hour) = HOUR_TRANSLATION[hour_block]
                year = datetime.now().year

                if summary == "-":
                    continue

                start_string = f"{year}-{month_number}-{day_of_the_month}T{start_hour}"
                ev_start = datetime.strptime(start_string, "%Y-%m-%dT%H:%M")
                end_string = f"{year}-{month_number}-{day_of_the_month}T{end_hour}"
                ev_end = datetime.strptime(end_string, "%Y-%m-%dT%H:%M")
                

                ev = Event(summary=summary, start=ev_start, end=ev_end)
                calendar.events.append(ev)

    return IcsCalendarStream.calendar_to_ics(calendar)

def parse_plansoft_tree(tree: BeautifulSoup) -> (dict, dict):
    hours = {} # map DAY: hours[][] "pon" -> 1-2 [1 1 1],  
    days = {} # map DAY: day[] "pon" -> 10 IV, 11 IV ...

    trs = tree.find_all("tr")
    day_regex = re.compile("^[0-9]+ [A-Z]+$")
    hour_regex = re.compile("^ [0-9]+-[0-9]+$") # NOTE the space at the start

    # initialize
    day_of_week = ""
    for tr in trs:
        tds = tr.find_all("td")
        if tds[0].string in DAYS:
            day_of_week = tds[0].string
            hours[day_of_week] = {}
            days[day_of_week] = []

    # import day numbers
    for tr in trs:
        tds = tr.find_all("td")
        if tds[0].string in DAYS:
            day_of_week = tds[0].string

        for td in tds:
            c = td.string
            if c is None:
                continue
            if day_regex.match(c):
                days[day_of_week].append(c)

    # import hours
    day_of_week = ""
    for tr in trs:
        tds = tr.find_all("td")
        if tds[0].string in DAYS:
            day_of_week = tds[0].string
        if day_of_week == "":
            continue
        
        num_days = len(days[day_of_week])
        for td in tds:
            c = td.string
            if c is None:
                continue
            if hour_regex.match(c):
                hours[day_of_week][c] = [None for x in range(num_days)]

    # finally parse the schedule
    day_of_week = ""
    for tr in trs:
        tds = tr.find_all("td")
        if tds[0].string in DAYS:
            day_of_week = tds[0].string
        if day_of_week == "":
            continue
        
        # ensure the first td is an hour
        if not hour_regex.match(tds[0].string):
            continue
        current_hour = tds[0].string
        h_pos = 0
        for td in tds[1:]:
            txt = td.get_text("|", strip=True)
            colspan = 1
            if "colspan" in td.attrs:
                colspan = int(td["colspan"])

            rowspan = 1
            if "rowspan" in td.attrs:
                rowspan = int(td["rowspan"])


            if len(txt) == 0:
                txt = "-"
            
            for c in range(colspan):
                hours[day_of_week][current_hour][h_pos] = (txt, rowspan)
                h_pos += 1

            if h_pos >= len(days[day_of_week]):
                break


    # expand rowspans
    for day_name in hours:
        POSSIBLE_HOURS = list(hours[day_name].keys())
        for hour_block in hours[day_name]:
            for h_pos, event in enumerate(hours[day_name][hour_block]):
                (txt, rowspan) = event
                if rowspan < 2:
                    continue
                
                row_index = POSSIBLE_HOURS.index(hour_block)
                row_index += 1 # let's start at 1 below
                for r in range(1, rowspan):
                    new_hour = POSSIBLE_HOURS[row_index]

                    last_idx = len(hours[day_name][new_hour]) - 1

                    # find all elements to the right of h_pos
                    # from n=-1 to n=h_pos copy to n++
                    for irightside in range(last_idx, h_pos, -1):
                        hours[day_name][new_hour][irightside] = hours[day_name][new_hour][irightside - 1]

                    # then insert at h_pos
                    hours[day_name][new_hour][h_pos] = (txt, 1)
                    row_index += 1

    return (hours, days)

def generate_ical(plansoft: str) -> str:
    tree = BeautifulSoup(plansoft, "html.parser")
    (hours, days) = parse_plansoft_tree(tree)
    return create_calendar(hours, days)

def get_html(url: str) -> str:
    resp = requests.get(url, timeout=20)
    if resp.status_code != 200:
        print(f"invalid status?? code?? {resp.status_code} for {url}")
        exit(1)
    resp.encoding = 'windows-1250'
    body = resp.text
    return body

def build_link_to_id(id: str) -> str:
    prefix_path = "https://wml.wat.edu.pl/wp-content/uploads/rozklady_zajec/"
    month = datetime.now().month
    year = datetime.now().year
    if month < 3:
        return f"{prefix_path}{year-1}_sem_zima/{id}.htm"
    elif month < 9:
        return f"{prefix_path}{year-1}_sem_lato/{id}.htm"
    return f"{prefix_path}{year}_sem_zima/{id}.htm"



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert plansoft link to a calendar file')
    parser.add_argument("--link", type=str, help="direct link to the html file")
    parser.add_argument("--id", type=str, help="html file id (like a group name)", default="WMT23AX1S1")
    parser.add_argument("--output", type=str, help="output file. preferably ending with .ics", default="calendar.ics")

    args = parser.parse_args()

    link = build_link_to_id(args.id)
    if args.link:
        link = args.link
    plan = get_html(link)
    ical = generate_ical(plan)

    with open(args.output, encoding="utf-8", mode="w") as f:
        f.write(ical)

    # with open("plansoft.html", encoding='windows-1250') as f:
    #     tree = BeautifulSoup(f, 'html.parser')