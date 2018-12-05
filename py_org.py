import datetime
import json
import re
from collections import defaultdict


class OrgEvent:
    title = None
    time_start = None
    time_end = None
    when = None
    dow = None
    attendees = []
    comments = []
    todo_list = []

    def __init__(self):
        self.attendees = []
        self.comments = []
        self.todo_list = []

    def run_time(self):
        minutes_start = minutes_total(self.time_start)
        minutes_end = minutes_total(self.time_end)
        return minutes_format(minutes_end - minutes_start)

    def __str__(self):
        result = []
        str_start = "{0} {1}. {2}".format(self.when, day_of_week(self.dow)[:2], self.time_start)
        str_end = "{0} {1}. {2}".format(self.when, day_of_week(self.dow)[:2], self.time_end)
        result.append("**** <{0}> {1}".format(str_start, self.title))
        result.append("     :PROPERTIES:")
        result.append("     Attendees: {0}".format(", ".join(self.attendees)))
        result.append("     :END:")
        result.append("     :LOGBOOK:")
        result.append("     CLOCK: [{0}]--[{1}] =>  {2}".format(str_start, str_end, self.run_time()))
        result.append("     :END:")
        for comment in self.comments:
            result.append("     {0}".format(comment))
        for todo in self.todo_list:
            result.append("***** TODO {0}".format(todo))
        return '\n'.join(str(x) for x in result)

    def parse(self, event_lines):
        for line in event_lines:
            if line.startswith("     :"):
                continue
            elif line.startswith("     Attendees: "):
                self.attendees = line.split(": ")[1].split(", ")
            elif line.startswith("     CLOCK: "):
                groups = re.findall("(\d{2}:\d{2})\]", line)
                self.time_start = groups[0]
                self.time_end = groups[1]
            elif line.startswith("***** TODO "):
                self.todo_list.append(line.split("***** TODO ")[1])
            elif line.startswith("     "):
                self.comments.append(line.split("     ")[1])


class OrgDay:
    dow = None
    events = None

    def __init__(self):
        self.events = []

    def add(self, json_obj):
        self.dow = json_obj["date_parsed"][2] - 1
        ev = OrgEvent()
        ev.dow = self.dow
        ev.when = json_obj["date0"]
        ev.title = json_obj["title0"]
        ev.time_start = parse_time(json_obj["time0"])
        ev.time_end = parse_time(json_obj["time1"])
        ev.comments = fetch_incrementing(json_obj, "comment")
        ev.todo_list = fetch_incrementing(json_obj, "todo")
        ev.attendees = json_obj["attendees0"].split(", ")
        self.events.append(ev)

    def __str__(self):
        result = []
        events_sorted = sorted(self.events, key=lambda x: x.time_start)
        for ev in events_sorted:
            result.append("*** {0} {1}".format(ev.when, day_of_week(self.dow)))
            result.append(ev)
        return '\n'.join(str(x) for x in result)

    def parse(self, day_lines):
        current_event = None
        event_lines = []
        for line in day_lines:
            if line.startswith("**** "):
                if current_event is not None:
                    current_event.parse(event_lines)
                    self.events.append(current_event)
                    event_lines = []
                current_event = OrgEvent()
                current_event.dow = self.dow
                groups = re.match("\*{4} <(\d{4}-\d{2}-\d{2}) \w{2}\. \d+:\d+> (.*)", line).groups()
                current_event.when = groups[0]
                current_event.title = groups[1]
            if not line.startswith("**** "):
                event_lines.append(line)
        if current_event is not None:
            current_event.parse(event_lines)
            self.events.append(current_event)


class OrgWeek:
    days = None

    def __init__(self):
        self.days = defaultdict(OrgDay)
        pass

    def add(self, json_obj):
        day = json_obj["date_parsed"][2]
        self.days[day].add(json_obj)

    def __str__(self):
        result = []
        days_sorted = sorted(self.days.keys())
        for i in days_sorted:
            result.append(self.days[i])
        return '\n'.join(str(x) for x in result)

    def parse(self, week_lines):
        current_day = None
        day_lines = []
        for line in week_lines:
            if line.startswith("*** "):
                if current_day is not None:
                    current_day.parse(day_lines)
                    self.days[current_day.dow] = current_day
                    day_lines = []
                current_day = OrgDay()
                parts = line.split(" ")
                ymd = parse_ymd(parts[1])
                current_day.dow = datetime.date(ymd[0], ymd[1], ymd[2]).isocalendar()[2] - 1
            if not line.startswith("*** "):
                day_lines.append(line)
        if current_day is not None:
            current_day.parse(day_lines)
            self.days[current_day.dow] = current_day


class OrgYear:
    year = None
    weeks = None

    def __init__(self):
        self.weeks = defaultdict(OrgWeek)
        pass

    def add(self, json_obj):
        self.year = json_obj["date_parsed"][0]
        week = json_obj["date_parsed"][1]
        self.weeks[week].add(json_obj)

    def __str__(self):
        result = []
        weeks_sorted = sorted(self.weeks.keys())
        for i in weeks_sorted:
            result.append("** {0}-W{1}".format(self.year, str(i).zfill(2)))
            result.append(self.weeks[i])
        return '\n'.join(str(x) for x in result)

    def parse(self, year_lines):
        current_week = None
        week_number = 0
        week_lines = []
        for line in year_lines:
            if line.startswith("** "):
                if current_week is not None:
                    current_week.parse(week_lines)
                    self.weeks[week_number] = current_week
                    week_lines = []
                current_week = OrgWeek()
                week_number = int(line.split("-W")[1])
            if not line.startswith("** "):
                week_lines.append(line)
        if current_week is not None:
            current_week.parse(week_lines)
            self.weeks[week_number] = current_week


class Org:
    years = None

    def __init__(self):
        self.years = defaultdict(OrgYear)

    def add_parse(self, json_str):
        obj = json.loads(json_str)
        ymd = parse_ymd(obj["date0"])
        obj["date_parsed"] = datetime.date(ymd[0], ymd[1], ymd[2]).isocalendar()
        year = ymd[0]  # year

        self.years[year].add(obj)

    def __str__(self):
        result = []
        years_sorted = sorted(self.years.keys())
        for i in years_sorted:
            result.append("* {0}".format(i))
            result.append(self.years[i])
        result.append("")
        return '\n'.join(str(x) for x in result)

    def parse(self, org_str):
        lines = org_str.split("\n")
        current_year = None
        year_lines = []
        for line in lines:
            if line.startswith("* "):
                if current_year is not None:
                    current_year.parse(year_lines)
                    self.years[current_year.year] = current_year
                    year_lines = []
                current_year = OrgYear()
                current_year.year = int(line.split(" ")[1])
            if not line.startswith("* "):
                year_lines.append(line)
        if current_year is not None:
            current_year.parse(year_lines)
            self.years[current_year.year] = current_year


def fetch_incrementing(json_obj, key):
    results = []
    count = 0
    res = json_obj.get(key + str(count), None)
    while res is not None:
        results.append(res)
        count += 1
        res = json_obj.get(key + str(count), None)
    return results


def parse_time(time_string):
    return "{0}:{1}".format(time_string[:2], time_string[2:])


def day_of_week(dow):
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dow]


def minutes_total(time_string):
    parts = list(map(lambda x: int(x), time_string.split(":")))
    return parts[0]*60 + parts[1]


def minutes_format(minute_string):
    hours = int(minute_string/60)
    minutes = minute_string % 60
    return "{0}:{1}".format(str(hours).zfill(2), str(minutes).zfill(2))


def parse_ymd(date_string):
    parts = date_string.split("-")
    return list(map(lambda x: int(x), parts))



