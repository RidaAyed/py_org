import datetime
import json
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


class Org:
    years = None

    def __init__(self):
        self.years = defaultdict(OrgYear)

    def add_parse(self, json_str):
        obj = json.loads(json_str)
        ydm = parse_ymd(obj["date0"])
        obj["date_parsed"] = datetime.date(ydm[0], ydm[1], ydm[2]).isocalendar()
        year = ydm[0]  # year

        self.years[year].add(obj)

    def __str__(self):
        result = []
        years_sorted = sorted(self.years.keys())
        for i in years_sorted:
            result.append("* {0}".format(i))
            result.append(self.years[i])
        return '\n'.join(str(x) for x in result)


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



