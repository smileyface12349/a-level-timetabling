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


class Choices:
    """Represents a list of student choices"""

    def __init__(self):
        self.by_student = {}  # student: [subjects]
        self.by_subject = {}  # subject: [students]

    def from_dict_by_student(self, by_student):
        """Helper method in case the dict form has already been generated"""
        self.by_student = by_student
        self._update_by_subject()

    def _update_by_subject(self):
        """This should be called every time the value changes"""
        self.by_subject = {}  # {subject: [student]}
        for student in self.by_student:
            subjects = self.by_student[student]
            for subject in subjects:
                if subject in self.by_subject:
                    self.by_subject[subject].append(student)
                else:
                    self.by_subject[subject] = [student]

    def add_student(self, student, *subjects):
        """Adds a new student choice"""
        if student in self.by_student:
            self.by_student[student] += list(subjects)
        else:
            self.by_student[student] = list(subjects)
        self._update_by_subject()


class Classes:
    """Represents allocated classes

    Can be accessed to get the students in each class, or which classes conflict with each other"""

    MAX_SIZE = 24
    MIN_SIZE = 4
    MAIN_BLOCKS = 4

    def __init__(self):
        self._main_blocks = [{'classes': [], 'conflicts': {}}]*self.MAIN_BLOCKS
        self._overflow_blocks = []

    def allocate(self, choices:Choices):
        """Allocates or re-allocates students to classes given their choices"""

        working_main_blocks = [{'classes': [], 'conflicts': {}}]*self.MAIN_BLOCKS
        working_overflow_blocks = []

        subjects_not_considered = choices.by_subject

        self.allocate_rec(subjects_not_considered, working_main_blocks, working_overflow_blocks)

    def allocate_rec(self, subjects_not_considered, working_main_blocks, working_overflow_blocks, best_possibility=None):
        if not subjects_not_considered:
            return

        possibilities = []

        # consider just the first subject - other subjects will be considered on future function calls
        subject = dict(subjects_not_considered).pop(0) # here, dict() ensures the parameter is passed by value, not by reference
        for block in self._main_blocks:
            # TODO: consider allocating subject to that block, resolving conflicts in any way that seems appropriate
            p_working_main_blocks = working_main_blocks
            p_working_overflow_blocks = working_overflow_blocks
            possibilities.append(self.allocate_rec(subjects_not_considered, p_working_main_blocks, p_working_overflow_blocks))

        # TODO: get best possibility
        return best_possibility


class LiveTimetable:
    """Stores the current timetable"""


class Event:
    """Represents an event in the timetable"""


class Unscheduled:
    """Stores all events that are yet to be scheduled"""
