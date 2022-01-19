import random
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
    OVERFLOW_THRESHOLD = 4  # threshold of conflicting students to attempt to allocate overflow blocks
    MAIN_BLOCKS = 4

    def __init__(self):
        self._main_blocks = [{'classes': [], 'conflicts': {}}]*self.MAIN_BLOCKS
        self._overflow_blocks = []

    def allocate(self, choices:Choices):
        """Allocates or re-allocates students to classes given their choices"""

        working_main_blocks = [{'classes': [], 'conflicts': {}}]*self.MAIN_BLOCKS
        working_overflow_blocks = []

        subjects_not_considered = choices.by_subject # subjects: [student]
        student_classes = {}  # subject: student: [classId]

        self.allocate_rec(subjects_not_considered, working_main_blocks, working_overflow_blocks, student_classes)

    def allocate_rec(self, subjects_not_considered, working_main_blocks, working_overflow_blocks, student_classes, best_possibility=None):
        if not subjects_not_considered:
            return

        possibilities = []

        # consider just the first subject - other subjects will be considered on future function calls
        subject = dict(subjects_not_considered).pop(0)  # here, dict() ensures the parameter is passed by value, not by reference
        for block in working_main_blocks:
            # Consider allocating subject to that block, resolving conflicts in any way that seems appropriate
            p_working_main_blocks = working_main_blocks
            p_working_overflow_blocks = working_overflow_blocks

            # get conflicts between this subject and that block
            conflicts = []
            non_conflicts = []
            for subject_in_block in block:
                if subject_in_block == subject:
                    for student_in_subject_in_block in student_classes[subject_in_block]:
                        conflicts.append(student_in_subject_in_block)
                else:
                    for student_in_subject_in_block in student_classes[subject_in_block]:
                        non_conflicts.append(student_in_subject_in_block)

            # Isolate conflicts to minimum number of classes possible
            if len(conflicts) < self.MAX_SIZE:  # all conflicts fit in one class
                conflict_class_id = self.generate_class_id(student_classes=student_classes)
                for student in conflicts:
                    if subject not in student_classes:
                        student_classes[subject] = {}
                    if student not in student_classes[subject]:
                        student_classes[subject][student] = []
                    student_classes[subject][student] = [conflict_class_id]
            # TODO: What if there are more than MAX_SIZE conflicts?
            if len(non_conflicts) < self.MAX_SIZE:  # all conflicts fit in one class
                taken = {}  # todo
                non_conflict_class_id = self.generate_class_id(taken)
                for student in conflicts:
                    if subject not in student_classes:
                        student_classes[subject] = {}
                    if student not in student_classes[subject]:
                        student_classes[subject][student] = []
                    student_classes[subject][student] = [non_conflict_class_id, conflict_class_id]
            # TODO: What if there are more than MAX_SIZE non conflicts?

            # CONSIDER: Put non-conflicts in this block and conflicts elsewhere
            # Class of non conflicts should go in this block
            p_working_main_blocks[block]['classes'].append(non_conflict_class_id)
            # Class of conflicts should go in a different block - try all
            for b in working_main_blocks:
                if b == block:
                    continue
                p_working_main_blocks[b]['classes'].append(conflict_class_id)
                # TODO: Need to properly consider conflicts with other blocks - should go back through recursion with it
                possibilities.append(
                    self.allocate_rec(subjects_not_considered, p_working_main_blocks, p_working_overflow_blocks,
                                      student_classes, best_possibility=best_possibility))
                p_working_main_blocks[b]['classes'].pop(-1)

            # CONSIDER: Move all conflicts to an overflow block, and allocate non-conflicts here
            # (but don't bother if greater than the overflow threshold)
            if len(conflicts) <= self.OVERFLOW_THRESHOLD:
                p_working_overflow_blocks.append({'classes': [conflict_class_id]})
                possibilities.append(
                    self.allocate_rec(subjects_not_considered, p_working_main_blocks, p_working_overflow_blocks,
                                      student_classes, best_possibility=best_possibility))

            # TODO: CONSIDER: Split up classes within the block instead

            possibilities.append(self.allocate_rec(subjects_not_considered, p_working_main_blocks, p_working_overflow_blocks, student_classes, best_possibility=best_possibility))

        # TODO: Determine which possibility is best
        best_possibility = random.choice(possibilities)

        return best_possibility

    def generate_class_id(self, student_classes=None, taken=None):
        """Generates a unique ID that is not taken

        EITHER student_classes OR taken can be provided (if both are provided, taken takes priority)
         - if neither are provided, there is a 1 in 2^32 chance of a collision

        :param student_classes: Current class allocations, of form {subject: {student: [class_id]}}
        :param taken: List of class IDs already used"""

        if not taken:
            taken = []  # list of all class ids that have been used
            if student_classes:
                for x in student_classes.keys():
                    for y in student_classes[x].keys():
                        taken.append(student_classes[x][y])

        while True:
            potential_id = str(random.randint(1, 2**32))
            if potential_id not in taken:
                break
        return potential_id


class LiveTimetable:
    """Stores the current timetable"""


class Event:
    """Represents an event in the timetable"""


class Unscheduled:
    """Stores all events that are yet to be scheduled"""
