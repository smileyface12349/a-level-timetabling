class Timetabler:
    """Responsible for generating the timetable

    Aims to minimise the number of conflicts using a heuristic algorithm
     - A priority system determines when conflicts are acceptable (e.g. meeting clashing with break time would be ok)

    Priorities:
     - 1: Very high priority (Music lessons, one-off events etc.)
     - 2: High priority (Lessons)
     - 3: Medium priority (Lunch slot, Meetings)
     - 4: Low priority (Break times, Non-lunch lunch time)
     - 5: No Priority (Entirely free time - no disruption at all)

    Note that the teachers should already be allocated to classes [There may be a function provided to do this that
    provides the optimal arrangement of teachers to minimise issues with the timetable]"""

    def __init__(self, blocks: int, overtime_blocks: int):
        """

        :param blocks: Number of blocks in a given day. A block is the smallest unit of time available (usually 5 mins)
        :param overtime_blocks: In the event a solution is not possible within the usual blocks, how many extra blocks
        are available to schedule activities in

        Classes, availability and other constraints can be added through the relevant functions
        """
        pass

    def add_class(self, teacher, students):
        """Adds a class to the scheduler

        :param teacher: The ID of the teacher """

    def add_teacher(self, name, working_hours, preferences):
        """Adds a teacher

        :param name:
        :param working_hours:
        :param preferences:
        :return:
        """