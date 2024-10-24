#!/usr/bin/env python3
import httpx
import argparse
import re
from bs4 import BeautifulSoup
from datetime import datetime
from ical.calendar import Calendar
from ical.event import Event
from ical.calendar_stream import IcsCalendarStream

DAYS = ["pon.", "wt.", "śr.", "czw.", "pt.", "sob.", "niedz."]
ROMAN_TO_MONTH = [
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
]
HOUR_TRANSLATION = {
    " 1-2": ("8:00", "9:35"),
    " 3-4": ("9:50", "11:25"),
    " 5-6": ("11:40", "13:15"),
    " 7-8": ("13:30", "15:05"),
    " 9-10": ("15:45", "17:20"),
    " 11-12": ("17:35", "19:10"),
    " 13-14": ("19:25", "21:00"),
}
HOUR_TRANSLATION_NEW = {
    " 1-2": ("8:00", "9:35"),
    " 3-4": ("9:50", "11:25"),
    " 5-6": ("11:40", "13:15"),
    " 7-8": ("13:30", "15:05"),
    " 9-10": ("16:00", "17:35"),
    " 11-12": ("17:50", "19:25"),
    " 13-14": ("19:40", "21:15"),
}


def log(level: str, message):
    level = level.upper()
    if level not in ["INFO", "ERROR"]:
        level = "INFO"
    print(f"[{level}] {message}")


def create_calendar(hours: dict, days: dict) -> str:
    calendar = Calendar()
    for day_name in hours:
        for hour_block in hours[day_name]:
            for h_pos, event in enumerate(hours[day_name][hour_block]):
                day_month = days[day_name][h_pos]
                (day_of_the_month, month_number_roman) = day_month.split(" ")
                month_number = ROMAN_TO_MONTH.index(month_number_roman) + 1
                summary = event[0]
                year = datetime.now().year
                if datetime.now().month >= 9:
                    if month_number < 9:
                        year += 1
                else:
                    if month_number >= 9:
                        year -= 1

                if summary == "-":
                    continue

                # Handle transition to new hours
                (start_hour, end_hour) = HOUR_TRANSLATION_NEW[hour_block]
                if year <= 2024 and month_number <= 11 and day_of_the_month < 4:
                    (start_hour, end_hour) = HOUR_TRANSLATION[hour_block]


                start_string = f"{year}-{month_number}-{day_of_the_month}T{start_hour}"
                ev_start = datetime.strptime(start_string, "%Y-%m-%dT%H:%M")
                end_string = f"{year}-{month_number}-{day_of_the_month}T{end_hour}"
                ev_end = datetime.strptime(end_string, "%Y-%m-%dT%H:%M")

                ev = Event(summary=summary, start=ev_start, end=ev_end)
                calendar.events.append(ev)

    return IcsCalendarStream.calendar_to_ics(calendar)


def parse_plansoft_tree(tree: BeautifulSoup) -> tuple[dict, dict]:
    hours = {}  # map DAY: hours[][] "pon" -> 1-2 [1 1 1],
    days = {}  # map DAY: day[] "pon" -> 10 IV, 11 IV ...

    trs = tree.find_all("tr")
    day_regex = re.compile("^[0-9]+ [A-Z]+$")
    hour_regex = re.compile("^ [0-9]+-[0-9]+$")  # NOTE the space at the start

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
                hours[day_of_week][c] = [None for _ in range(num_days)]

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
                row_index += 1  # let's start at 1 below
                for _ in range(1, rowspan):
                    new_hour = POSSIBLE_HOURS[row_index]

                    last_idx = len(hours[day_name][new_hour]) - 1

                    # find all elements to the right of h_pos
                    # from n=-1 to n=h_pos copy to n++
                    for irightside in range(last_idx, h_pos, -1):
                        hours[day_name][new_hour][irightside] = hours[day_name][
                            new_hour
                        ][irightside - 1]

                    # then insert at h_pos
                    hours[day_name][new_hour][h_pos] = (txt, 1)
                    row_index += 1

    return (hours, days)


def generate_ical(plansoft: str) -> str:
    tree = BeautifulSoup(plansoft, "html.parser")
    (hours, days) = parse_plansoft_tree(tree)
    return create_calendar(hours, days)


def get_html(url: str) -> str:
    client = httpx.Client(default_encoding="windows-1250")
    resp = client.get(url, timeout=20)
    return resp.text


def build_link_to_id(id: str) -> str:
    prefix_path = "https://wml.wat.edu.pl/wp-content/uploads/rozklady_zajec/"
    month = datetime.now().month
    year = datetime.now().year
    if month < 3:
        return f"{prefix_path}{year-1}_sem_zima/{id}.htm"
    elif month < 9:
        return f"{prefix_path}{year-1}_sem_lato/{id}.htm"
    return f"{prefix_path}{year}_sem_zima/{id}.htm"


def main():
    parser = argparse.ArgumentParser(
        description="Convert plansoft link to a calendar file"
    )
    parser.add_argument("--link", type=str, help="direct link to the html file")
    parser.add_argument(
        "--id", type=str, help="html file id (like a group name)", default="WMT23AX1S1"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="output file. preferably ending with .ics",
        default="calendar.ics",
        required=True,
    )
    log("INFO", "plan-to-ics starts")

    args = parser.parse_args()

    if (not args.id) and (not args.link):
        log("ERROR", "no target passed (neither --id nor --link)")
        return

    link = build_link_to_id(args.id)
    log("INFO", "parsed argv")
    if args.link:
        log("INFO", "using --link instead of --id")
        link = args.link
    log("INFO", f"getting {link=}")
    try:
        plan = get_html(link)
        log("INFO", f"downloaded plansoft document -- {len(plan)} bytes")
        ical = generate_ical(plan)
        log("INFO", f"generated calendar file -- {len(ical)} bytes")

        log("INFO", f"writing to {args.output}")
        try:
            with open(args.output, encoding="utf-8", mode="w") as f:
                n = f.write(ical)
                log("INFO", f"{n} bytes written successfully")
        except OSError:
            log("ERROR", "could not write to --output (check permissions)")

        log("INFO", "plan-to-ics finishes")
    except httpx.HTTPStatusError as e:
        log("ERROR", f"invalid status code -- {e.response.status_code}")
    except httpx.TransportError as e:
        log("ERROR", "connection error")
    except httpx.DecodingError as e:
        log("ERROR", "can't decode response")
    except httpx.HTTPError as e:
        log("ERROR", f"generic http error -- {e}")
    except Exception as e:
        log("ERROR", f"generic error -- {e}")

    # with open("plansoft.html", encoding='windows-1250') as f:
    #     tree = BeautifulSoup(f, 'html.parser')


if __name__ == "__main__":
    main()
