import datetime
import random
from typing import List, Sequence, Optional, Tuple

from src.django_project.timetable.models import Lesson, User


def should_stop(current_population, previous_population, iterations):
    if iterations > 1000:
        return True
    else:
        return False


class Population:
    """Represents a population of timetables for use in the genetic algorithm"""

    def __init__(self, timetable_init_kwargs,
                 popsize=100, num_parents=50,
                 mutation_amount=2, guaranteed_parent_survival=5,
                 stopping_condition=should_stop,
                 first_day: Optional[datetime.datetime] = None, days: int = 1,
                 time_per_day: int = 114, seconds_per_unit_time: float = 300,
                 day_start=datetime.time(8, 30, 0)):
        """

        :param popsize: The population size
        :param stopping_condition: A function taking in:
         - the current population (of type Population)
         - previous population (THIS WILL BE NONE ON THE FIRST ITERATION)
         - the number of iterations / generations
         and returning True to stop and False to continue
        """

        if first_day:
            self.first_day = first_day
        else:
            self.first_day = datetime.datetime.now()
        self.days = days
        self.time_per_day = time_per_day
        self.seconds_per_unit_time = seconds_per_unit_time
        self.day_start = day_start

        self.popsize = popsize
        self.num_parents = num_parents
        self.guaranteed_surviving_parents = guaranteed_parent_survival
        self.stopping_condition = stopping_condition
        self.generations = 0
        self.mutation_amount = mutation_amount

        if self.num_parents > self.popsize:
            raise ValueError("Number of parents cannot be greater than size of population")
        if self.guaranteed_surviving_parents > self.num_parents:
            raise ValueError("Surviving parents cannot be more than the number of parents")
        if self.popsize < 1:
            raise ValueError("Population must be positive")

        self.population: list[tuple[Timetable, float]] = []  # (timetable, cost)
        for x in range(self.popsize):
            self.population.append((Timetable(**timetable_init_kwargs).random(), float('inf')))

    def start(self):
        """Iterate over the solution until self.stopping_condition returns True
         self.stopping_condition should have a fallback condition on the number of iterations to prevent an infinite loop"""

        previous = None
        self.population = self.evaluate_all_costs(self.population)
        while not self.stopping_condition(self, previous, self.generations):
            previous = self.copy()
            self.iterate()
            self.generations += 1

    def iterate(self):
        """Performs one iteration of the genetic algorithm on the current population"""

        parents = self.choose_parents()
        offspring = self.generate_offspring(parents)
        candidates = parents + offspring
        self.population = self.choose_new_population(candidates)

    def choose_new_population(self, candidates):
        """Chooses the new population from the list of candidates
        The value of the cost function should be either the correct value or infinity if not evaluated"""
        new_population = []
        previous_best_cost = min(candidates, key=lambda t, c: c)[1]

        # carry forward the best solutions from the previous iteration
        for x in range(self.guaranteed_surviving_parents):
            new_population.append(candidates.pop(0))

        # choose the remaining solutions randomly, with a probability proportional to the cost function
        # sorting the list based on cost would be ideal however is too expensive
        while len(new_population) < self.popsize:
            i = random.randint(0, len(candidates)-1)
            candidate = candidates[i]

            # evaluate the cost function if not already
            if candidate[1] == float('inf'):
                candidate[1] = candidate[0].cost()

            # choose with probability (roughly) proportional to the value of the cost function
            #   - this will be incorrect if an uncalculated cost is greater than that of the previous iteration
            p = candidate[1] / previous_best_cost
            if p > random.uniform(0, 1):
                new_population.append(candidates.pop(i))

        return new_population

    def evaluate_all_costs(self, population):
        """Evaluates the cost function for every timetable in the given population"""

        for i, timetable in enumerate(population):
            timetable, cost = timetable
            timetable: Timetable
            population[i][1] = timetable.cost()

        return population

    def choose_parents(self):
        """Chooses the best parents from the population to mate"""

        candidates = self.population
        parents = []

        # choose the best parents
        for x in range(self.num_parents):
            best_parent = min(candidates, key=lambda t, c: c)
            parents.append(best_parent)
            candidates.remove(best_parent)

        return parents

    def generate_offspring(self, parents):
        """Generates all the offspring"""

        num_offspring = self.popsize - self.num_parents
        offspring = []

        for x in range(num_offspring):
            parent1 = random.choice(parents)
            parent2 = random.choice(parents)
            offspring.append(self.crossover(parent1, parent2))

        return offspring

    def crossover(self, parent1, parent2):
        """Returns one offspring containing half information from each parent"""

        new_lessons = []
        for day in range(self.days):
            potential_new_lessons = parent1.lessons[day] + parent2.lessons[day]
            random.shuffle(potential_new_lessons)
            for x in range(len(potential_new_lessons)//2):
                new_lessons.append(potential_new_lessons.pop(0))

        timetable = Timetable(lessons=new_lessons, first_day=self.first_day, days=self.days, time_per_day=self.time_per_day, seconds_per_unit_time=self.seconds_per_unit_time, day_start=self.day_start)
        return timetable, float('inf')  # the cost function may not be needed, so it does not need to be executed here

    def mutate(self, offspring):
        """Randomly changes the offspring slightly"""

        for timetable in offspring:
            timetable.mutate()

        return offspring


class Timetable:
    """Represents a potential timetable for a given period of time"""

    def __init__(self, first_day: Optional[datetime.datetime] = None, days: int = 1, time_per_day: int = 114, seconds_per_unit_time: float = 300, day_start=datetime.time(8, 30, 0), unscheduled_lessons=None, lessons=None):
        if first_day:
            self.first_day = first_day
        else:
            self.first_day = datetime.datetime.now()
        self.days = days
        self.time_per_day = time_per_day
        self.seconds_per_unit_time = seconds_per_unit_time
        self.day_start = day_start

        if unscheduled_lessons:
            self.unscheduled_lessons = unscheduled_lessons
        else:
            self.unscheduled_lessons = []
            per_class = {}
            for unscheduled_lesson in Lesson.objects.filter(fixed=False).exclude(start__lte=datetime.datetime.now()):
                if unscheduled_lesson.group in per_class:
                    per_class[unscheduled_lesson.group] += 1
                else:
                    per_class[unscheduled_lesson.group] = 1

                if per_class[unscheduled_lesson.group] <= days:  # this helps to reduce the possibilities to consider
                    self.unscheduled_lessons.append(unscheduled_lesson)

        if not lessons:
            self.lessons = {}  # format {day: lesson} of type {int: Lesson}
            # Lesson objects will have their start time updated (but will NOT be saved)

    def random(self):
        """Generates a completely random solution
        All solutions should be equally likely, EXCEPT those involving clashes
        This algorithm makes some attempt to minimise clashes while being quick to execute"""

        # for each (randomly ordered) teacher...
        for day in range(self.days):
            dt = self.first_day + datetime.timedelta(days=day)
            after = dt.replace(day=0, minute=0, hour=0)  # this should be 0 anyway if first_day is actually a day
            before = dt.replace(day=23, hour=59, minute=59, second=59)
            for teacher in User.objects.filter(user_type__exact='teacher').order_by('?'):
                # for each (randomly ordered) lesson that involves this teacher
                for lesson in Lesson.objects.filter(group_id__link__user_id__id__exact=teacher.id, start__gte=after, start__lte=before).order_by('id'):
                    # TODO: Randomly choose from one of the teacher's classes
                    # try to schedule at random time
                    gaps = self.get_gaps(user_id=teacher.id)
                    random.shuffle(gaps)
                    for gap_start, gap in gaps:  # for each (random) gap,
                        if gap > lesson.duration + 1:  # if there's enough space for a lesson (need at least 1 unit either side)
                            if gap < lesson.duration * 1.5:  # if there's not much space...
                                lesson.start = gap_start + 1  # schedule for start of gap (plus 1 unit break)
                            else:
                                latest_end = gap_start + gap - 2
                                lesson.start = random.randint(gap_start, latest_end - lesson.duration)  # allocate to random position
                            self.lessons[day] = lesson
                            break
                        else:
                            continue
                    else:  # this triggers if the end of the loop is reached without a break statement
                        break  # if no time available to schedule, break

                # this teacher's day is now somewhat filled with lessons that do not clash

        return self

    def get_gaps(self, user_id, days=None) -> List[Tuple[int, int]]:
        """Gets a list of the duration of every gap on the given day, in time units

        Days should be a list of numbers, each indicating the number of days since first_day

        Returns dict of form [(start of gap, length of gap)] of type [(int, int)]"""
        if not days:
            days = range(self.days)

        previous = None
        gaps = []
        for day in days:
            for lesson in self.lessons[day]:
                if previous:
                    gaps.append((previous, lesson.start - previous))
                previous = lesson.start

        return gaps

    def cost(self):
        """Evaluates the cost function for the given solution"""
        cumulative_cost = 0
        # TODO
        return 0

    def fitness(self):
        """Returns the fitness value for a solution
        This is simply the negative of the cost value"""
        return -self.cost()

    def mutate(self, mutate_lessons_per_day=2):
        """Mutates the given solution (for use in a genetic algorithm)
        NOTE: The same lesson could be mutated twice (although unlikely)"""

        for day in range(self.days):
            for x in range(mutate_lessons_per_day):
                i = random.randint(0, len(self.lessons[day])-1)
                lesson = self.lessons[day][i]
                latest_time = self.time_per_day - lesson.duration
                lesson.start = random.randint(0, latest_time)  # change start time to random point in day

        return self

    def add(self):
        """Adds all lessons contained within this timetable into the database"""
        # TODO


class PotentiallyScheduledLesson(Lesson):
    """A Lesson used as part of a Timetable

    Notably, this abstracts the start time to make computation easier"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start = None  # override this field with abstracted start time
