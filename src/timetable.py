import time

class Timetabler:
    """Responsible for generating the timetable
    """

    def __init__(self, periods: int, overtime_periods: int):
        """
        :param periods: Number of periods in a given day. A period is the smallest unit of time available (usually 5 mins)
        :param overtime_periods: In the event a solution is not possible within the usual periods, these extra periods
        are available for scheduling
        """
        self.timetable = LiveTimetable()
        self.classes = Classes()
        self.unscheduled = Unscheduled()

    def update(self):
        """Updates the timetable with all newly scheduled lessons"""

    def loop(self, interval: float, stop_after:float = 0):
        """Repeatedly calls .update() every interval seconds
        Optional: stop after a given number of seconds
        Blocking call"""
        start = time.time()
        while True:
            self.update()
            time.sleep(interval)
            if stop_after and time.time() - start >= stop_after:
                break

    def setup(self):
        """Allocates classes given students' subject choices"""
        self.classes.allocate()


class Classes:
    """Represents allocated classes

    Can be accessed to get the students in each class, or which classes conflict with each other"""

    def allocate(self):
        """Allocates or re-allocates students to classes given their choices"""


class LiveTimetable:
    """Stores the current timetable"""


class Event:
    """Represents an event in the timetable"""


class Unscheduled:
    """Stores all events that are yet to be scheduled"""
