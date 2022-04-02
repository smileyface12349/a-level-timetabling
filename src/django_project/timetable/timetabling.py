import datetime
import math
import random
from typing import List, Sequence, Optional, Tuple

from src.django_project.timetable.models import Lesson, User, Group


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

        best, best_cost = self.select_best_solution()

        return best

    def iterate(self):
        """Performs one iteration of the genetic algorithm on the current population"""

        parents = self.choose_parents()
        offspring = self.generate_offspring(parents)
        candidates = parents + offspring
        self.population = self.choose_new_population(candidates)

    def select_best_solution(self):
        """Chooses the best solution, re-evaluating the cost function for all"""
        self.population = self.evaluate_all_costs(self.population)
        best = None, float('inf')
        for timetable, cost in self.population:
            if cost < best[1]:
                best = timetable, cost

        return best

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
            # higher cost is worse, so this gives the probability that it will fail
            if p < random.uniform(0, 1):
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

        timetable = Timetable(lessons=new_lessons, first_day=self.first_day, days=self.days,
                              time_per_day=self.time_per_day, seconds_per_unit_time=self.seconds_per_unit_time,
                              day_start=self.day_start)
        return timetable, float('inf')  # the cost function may not be needed, so it does not need to be executed here

    def mutate(self, offspring):
        """Randomly changes the offspring slightly"""

        for timetable in offspring:
            timetable.mutate()

        return offspring


class Timetable:
    """Represents a potential timetable for a given period of time"""

    def __init__(self, first_day: Optional[datetime.datetime] = None, days: int = 1, time_per_day: int = 114,
                 seconds_per_unit_time: float = 300, day_start=datetime.time(8, 30, 0), year_start=None,
                 unscheduled_lessons=None, group_data=None, desired_allocations=None, lessons=None):
        if first_day:
            self.first_day = first_day
        else:
            self.first_day = datetime.datetime.now()
        self.days = days
        self.time_per_day = time_per_day
        self.seconds_per_unit_time = seconds_per_unit_time
        self.day_start = day_start
        self.desired_allocations = desired_allocations

        if year_start:
            self.year_start = year_start
        else:
            first_lesson = Lesson.objects.order_by('start')[:1].get()
            self.year_start = first_lesson.start

        if unscheduled_lessons:
            self.unscheduled_lessons = unscheduled_lessons
            random.shuffle(self.unscheduled_lessons)
        else:
            self.unscheduled_lessons = []
            per_class = {}
            for unscheduled_lesson in Lesson.objects.filter(fixed=False).exclude(start__lte=first_day):
                if unscheduled_lesson.group in per_class:
                    per_class[unscheduled_lesson.group] += 1
                else:
                    per_class[unscheduled_lesson.group] = 1

                if per_class[unscheduled_lesson.group] <= days:  # this helps to reduce the possibilities to consider
                    self.unscheduled_lessons.append(unscheduled_lesson)
            random.shuffle(self.unscheduled_lessons)

        if group_data:
            self.group_data = group_data
        else:
            self.group_data = {}
            for group in Group.objects.filter():
                previous = None
                time_allocated = 0
                for lesson in Lesson.objects.filter(group_id__id__exact=group.id, start__lte=datetime.datetime.now()).order_by('start'):  # oldest first
                    previous = lesson
                    time_allocated += lesson.duration
                days_since_previous = (datetime.datetime.now().replace(hour=0, minute=0, second=0) - previous.start.replace(hour=0, minute=0, second=0)).days
                self.group_data[group.id] = [time_allocated, days_since_previous]

        if not lessons:
            self.lessons = {}  # format {day: lesson} of type {int: Lesson}
            # Lesson objects will have their start time updated (but will NOT be saved)

    def random(self, threshold=100):
        """Generates a random solution
        This algorithm makes some attempt to minimise teacher clashes while being quick to execute"""

        counter = 0
        for lesson in self.unscheduled_lessons:
            lesson:PotentiallyScheduledLesson
            teacher = self.get_teacher(lesson)
            day = random.randint(0, self.days-1)
            gaps = self.get_gaps(user_id=teacher.id, days=[day], random_order=True)

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
                counter += 1
                if counter > threshold:
                    break

        return self

    def get_teacher(self, lesson:'PotentiallyScheduledLesson'):
        """Gets a teacher who teaches the given lesson
        Teachers are cached, so the cached version will be returned upon any future calls"""
        if not hasattr(lesson, 'teacher'):
            lesson.teacher = User.objects.filter(link__class_id__lesson__id__exact=lesson.id, user_type__exact='teacher')[:1].get()
        return lesson.teacher

    def get_gaps(self, user_id, days=None, random_order=False) -> List[Tuple[int, int]]:
        """Gets a list of the duration of every gap on the given day, in time units

        Days should be a list of numbers, each indicating the number of days since first_day

        Returns dict of form [(start of gap, length of gap)] of type [(int, int)]"""
        if not days:
            days = range(self.days)

        previous = None
        gaps = []
        for day in days:
            sorted(self.lessons[day])
            for lesson in self.lessons[day]:
                if previous:
                    gaps.append((previous, lesson.start - previous))
                previous = lesson.start

        if random_order:
            random.shuffle(gaps)

        return gaps

    def get_gap_cost(self, gap_length):
        """Returns the value to add to the cost function for a gap of length gap_length, in time units
        Gaps should never be negative, but if so this function will return 0"""
        if gap_length == 0:
            return 10
        # 1 is the perfect length -> 0 is returned
        elif gap_length in (2, 3):
            return 5
        elif gap_length == 3:
            return 2
        elif gap_length == 4:
            return 1
        else:
            return 0

    def cost(self):
        """Evaluates the cost function for the current solution"""
        POINTS_PER_TEACHER_CLASH = 1000
        POINTS_PER_STUDENT_CLASH = 10
        MAX_LOAD_CONSTANT = 23  # max load = c ln c, where c is this value
        EARLY_FINISH_CONSTANT = 10
        EVEN_ALLOCATION_CONSTANT_A = 0.4
        EVEN_ALLOCATION_CONSTANT_B = 8
        WEIGHTING_OF_DIFF = 100
        VARIETY_BASE = 2
        VARIETY_COEFFICIENT = 1

        total_cost = 0
        for day in range(self.days):
            # constraints 1 & 2: clashes
            teacher_clashes = 0
            student_clashes = 0
            schedules = {}  # {user_id: [time_slot]}
            for lesson in self.lessons:
                for user in lesson.get_users():
                    clashes = 0
                    if user.id not in schedules:
                        schedules[user.id] = []
                    for x in range(lesson.duration):
                        time_slot = lesson.start + x
                        if time_slot in schedules[user.id]:
                            clashes += 1
                        else:
                            schedules[user.id].append(time_slot)
                    if user.user_type == 'teacher':
                        teacher_clashes += clashes
                    else:
                        student_clashes += clashes
            clashes_cost = POINTS_PER_STUDENT_CLASH * student_clashes + POINTS_PER_TEACHER_CLASH * teacher_clashes

            # constraint 3: even allocation of lesson times
            def sigmoid(a):
                return 1 / (1 + math.exp(-a))
            weighting = sigmoid(EVEN_ALLOCATION_CONSTANT_A + EVEN_ALLOCATION_CONSTANT_B * (self.first_day - self.year_start).days)
            diffs = 0
            for group_id in self.group_data:
                diff = abs(self.group_data[group_id][0] - self.desired_allocations[group_id]) / self.desired_allocations[group_id]
                diffs += diff
            even_allocation_cost = WEIGHTING_OF_DIFF * weighting * diffs

            # NOTE: constraint 4 is being computed with constraint 7

            # constraint 5: variety of subjects
            variety_cost = 0
            for group_id in self.group_data:
                variety_cost += VARIETY_COEFFICIENT * (VARIETY_BASE ** self.group_data[group_id][1])

            # constraint 6: max daily workload
            daily_workload_cost = 0
            for user_id in schedules:
                # NOTE: It is assumed that if any clashes occur, the user will miss out on
                # all but one of the concurrent events, so it does not contribute to their overall workload
                daily_workload_cost += max(math.exp(len(schedules[user_id])/MAX_LOAD_CONSTANT)-MAX_LOAD_CONSTANT, 0)

            # constraint 7: gaps
            gaps_cost = 0
            for user_id in schedules:  # NOTE: schedules is only used for a list of user ids
                gaps = self.get_gaps(user_id)
                for gap in gaps:
                    gaps_cost += self.get_gap_cost(gap)

            # constraint 8: early finish time
            early_finish_cost = 0
            for user_id in schedules:
                finish_time = max(schedules[user_id])
                early_finish_cost += finish_time / EARLY_FINISH_CONSTANT

            debug_info = {
                'teacher clashes': teacher_clashes,
                'student clashes': student_clashes,
                'clashes cost': clashes_cost,
                'total diffs': diffs,
                'even allocation cost': even_allocation_cost,
                'variety cost': variety_cost,
                'daily workload cost': daily_workload_cost,
                'gaps cost': gaps_cost,
                'early finish cost': early_finish_cost
            }

            total_cost += clashes_cost + even_allocation_cost + variety_cost + daily_workload_cost + gaps_cost + early_finish_cost

        return total_cost

    def fitness(self):
        """Returns the fitness value for a solution
        This is simply the negative of the cost value"""
        return -self.cost()

    def mutate(self, mutate_lessons_per_day=2):
        """Mutates the given solution (for use in a genetic algorithm)
        NOTE: The same lesson could be mutated twice (although unlikely)"""

        for day in range(self.days):
            for x in range(mutate_lessons_per_day):
                n = random.randint(1, 3)
                if n == 1:
                    # mutate start time of random lesson
                    i = random.randint(0, len(self.lessons[day])-1)
                    lesson = self.lessons[day][i]
                    latest_time = self.time_per_day - lesson.duration
                    lesson.start = random.randint(0, latest_time)
                elif n == 2:
                    # delete a random lesson
                    self.lessons[day].pop(random.randint(0, len(self.lessons[day])-1))
                elif n == 3:
                    # add a random lesson
                    lesson = self.unscheduled_lessons.pop(random.randint(0, len(self.unscheduled_lessons)-1))
                    latest_time = self.time_per_day - lesson.duration
                    lesson.start = random.randint(0, latest_time)
                    self.lessons[day].append(lesson)

        return self

    def add(self):
        """Update the database to include the start times for all lessons currently stored within this object"""
        # TODO


class PotentiallyScheduledLesson(Lesson):
    """A Lesson used as part of a Timetable
    Notably, this abstracts the start time to make computation easier"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start = None  # override this field with abstracted start time
        self.users = None

    def get_users(self):
        """Retrieves all users in this lesson, caching the result for subsequent queries"""
        if not self.users:
            self.users = User.objects.filter(link__group_id__lesson__id__exact=self.id)
        return self.users
