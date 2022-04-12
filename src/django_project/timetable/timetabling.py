import copy
import datetime
import math
import random
from typing import List, Optional, Tuple

from celery import Celery
from celery.schedules import crontab

from .models import Lesson, User, Group

app = Celery()


@app.task(run_every=crontab(hour=20, minute=0))
def schedule_lessons(iterations=10, look_ahead_period=14):
    """Creates a timetable using the unscheduled lessons from the database"""
    base_day = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, hour=0, second=0)
    for x in range(look_ahead_period):
        day = base_day + datetime.timedelta(days=x)
        end_of_day = day.replace(hour=23, minute=59, second=59)
        if day.weekday() <= 4:  # a weekday
            if not Lesson.objects.filter(start__gte=day, start__lte=end_of_day):
                print('-----------')
                print(f"SCHEDULING {day}")
                best_result: Optional[Timetable] = None
                for x in range(iterations):
                    print(f"Iteration: {x+1}")
                    population = Population(year_start=base_day, first_day=base_day + datetime.timedelta(days=x))
                    output: Timetable = population.start()
                    if best_result is None or output.get_cost() < best_result.get_cost():
                        best_result = output

                print(f"Adding best result (cost: {best_result.get_cost()})")
                best_result.add()

                for lesson in best_result.lessons[0]:
                    # group = Group.objects.filter(group_id__exact=lesson.group_id)[:1].get()
                    new_lesson = Lesson()
                    new_lesson.group_id = lesson.group_id
                    duration = random.randint(6, 24)
                    new_lesson.duration = datetime.timedelta(seconds=duration * 300)
                    new_lesson.topic = f"Automatically generated while timetabling"
                    new_lesson.fixed = False
                    new_lesson.save()


def should_stop(current_population, iterations):
    if iterations >= 100:
        return True
    else:
        return False


def get_unscheduled_lessons(first_day, days=1, seconds_per_unit_time: float = 300):
    unscheduled_lessons = []
    per_class = {}
    for unscheduled_lesson in Lesson.objects.filter(fixed=False).exclude(start__lte=first_day):
        unscheduled_lesson = PotentiallyScheduledLesson(unscheduled_lesson, seconds_per_time_unit=seconds_per_unit_time)

        if unscheduled_lesson.group_id in per_class:
            per_class[unscheduled_lesson.group_id] += 1
        else:
            per_class[unscheduled_lesson.group_id] = 1

        if per_class[unscheduled_lesson.group_id] <= days:  # this helps to reduce the possibilities to consider
            unscheduled_lessons.append(unscheduled_lesson)

    return unscheduled_lessons


def get_group_data():
    group_data = {}
    for group in Group.objects.filter():
        previous = None
        time_allocated = 0
        for lesson in Lesson.objects.filter(group_id__id__exact=group.id,
                                            start__lte=datetime.datetime.now(tz=datetime.timezone.utc)).order_by(
            'start'):  # oldest first
            previous = lesson
            time_allocated += lesson.duration.total_seconds()
            days_since_previous = (datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0)
                                  - previous.start.replace(tzinfo=datetime.timezone.utc, hour=0, minute=0, second=0)).days
        group_data[group.id] = [time_allocated, days_since_previous]

    return group_data


def get_year_start():
    first_lesson = Lesson.objects.order_by('start')[:1].get()
    year_start = first_lesson.start
    if not year_start:  # if no lessons in database
        dt = datetime.datetime.now(datetime.timezone.utc)
        if dt.month < 9:  # jan - aug
            # previous september
            year_start = datetime.datetime(year=dt.year - 1, month=9, day=1, tzinfo=datetime.timezone.utc)
        else:
            # in current year
            year_start = datetime.datetime(year=dt.year, month=9, day=1, tzinfo=datetime.timezone.utc)

    return year_start


def schedule(*args, **kwargs):
    """A helper function to generate the best timetable using a genetic algorithm"""
    population = Population(*args, **kwargs)
    return population.start()


class Population:
    """Represents a population of timetables for use in the genetic algorithm"""

    def __init__(self, timetable_init_kwargs=None, desired_allocations=None,
                 popsize=200, num_parents=50, num_offspring=100,
                 mutation_amount=3, mutation_chance=0.7, guaranteed_parent_survival=5,
                 stopping_condition=should_stop, random_lesson_skip_probability: float = 0.2,
                 first_day: Optional[datetime.datetime] = None, days: int = 1,
                 time_per_day: int = 114, seconds_per_unit_time: float = 300,
                 desired_lessons: int = 44,
                 day_start=datetime.timedelta(hours=8, minutes=30), year_start=None):
        """
        :param popsize: The population size
        :param stopping_condition: A function taking in:
         - the current population (of type Population)
         - previous population (THIS WILL BE NONE ON THE FIRST ITERATION)
         - the number of iterations / generations
         and returning True to stop and False to continue
        """

        if desired_allocations is None:
            self.desired_allocations = {}
        else:
            self.desired_allocations = desired_allocations
        if timetable_init_kwargs is None:
            timetable_init_kwargs = {}
        self.timetable_init_kwargs = timetable_init_kwargs
        if first_day:
            self.first_day = first_day
        else:
            self.first_day = datetime.datetime.now(datetime.timezone.utc)
        self.days = days
        self.time_per_day = time_per_day
        self.seconds_per_unit_time = seconds_per_unit_time
        self.day_start = day_start
        self.desired_lesson_time = desired_lessons

        self.popsize = popsize
        self.num_parents = num_parents
        self.num_offspring = num_offspring
        self.guaranteed_surviving_parents = guaranteed_parent_survival
        self.stopping_condition = stopping_condition
        self.generations = 0
        self.mutation_amount = mutation_amount
        self.mutation_chance = mutation_chance
        self.random_lesson_skip_probability = random_lesson_skip_probability

        self.unscheduled_lessons = get_unscheduled_lessons(self.first_day, self.days, self.seconds_per_unit_time)
        self.group_data = get_group_data()
        self.all_students = []
        for group_id in self.group_data:
            for student in User.objects.filter(user_type='student', link__group_id__id__exact=group_id):
                if student not in self.all_students:
                    self.all_students.append(student)
        if year_start:
            self.year_start = year_start
        else:
            self.year_start = get_year_start()

        if self.num_parents > self.popsize:
            raise ValueError("Number of parents cannot be greater than size of population")
        if self.guaranteed_surviving_parents > self.num_parents:
            raise ValueError("Surviving parents cannot be more than the number of parents")
        if self.popsize < 1:
            raise ValueError("Population must be positive")

        for group_id in self.group_data:
            # default desired allocations in case it is not provided
            if group_id not in self.desired_allocations:
                self.desired_allocations[group_id] = 1
                print(f"Warning: Group {group_id} had no desired allocation. Set to 1")

        self.population: List[Timetable] = []
        for x in range(self.popsize):
            self.population.append(Timetable(first_day=self.first_day, days=self.days, time_per_day=self.time_per_day,
                                             seconds_per_unit_time=self.seconds_per_unit_time, day_start=self.day_start,
                                             desired_allocations=self.desired_allocations, group_data=self.group_data,
                                             random_lesson_skip_probability=self.random_lesson_skip_probability,
                                             desired_lesson_time=self.desired_lesson_time, all_students=self.all_students,
                                             year_start=self.year_start, **timetable_init_kwargs).random())

    def start(self):
        """Iterate over the solution until self.stopping_condition returns True
         self.stopping_condition should have a fallback condition on the number of iterations to prevent an infinite loop"""

        # print(f"Timetabling...")
        self.population = self.evaluate_all_costs(self.population)
        while not self.stopping_condition(self, self.generations):
            # print(f"Iteration: {self.generations}")
            self.iterate()
            self.generations += 1

        # print('Selecting best solution')
        best = self.select_best_solution()

        # print("Timetabling complete!")

        return best

    def iterate(self):
        """Performs one iteration of the genetic algorithm on the current population"""

        parents = self.choose_parents()
        offspring = self.generate_offspring(list(parents))
        candidates = list(self.population + offspring)
        self.population = self.choose_new_population(candidates)
        # print(f"Best Cost: {self.select_best_solution(evaluate_costs=False).get_cost():.2f}")

    def select_best_solution(self, evaluate_costs=True):
        """Chooses the best solution, re-evaluating the cost function for all"""
        # if evaluate_costs:
        #     self.population = self.evaluate_all_costs(self.population)

        # best = None
        # for timetable in self.population:
        #     if best is None or timetable.get_cost() < best.get_cost():
        #         best = timetable

        best = min(self.population, key=lambda t: t.get_cost())

        return best

    def choose_new_population(self, candidates):
        """Chooses the new population from the list of candidates
        The value of the cost function should be either the correct value or infinity if not evaluated"""
        new_population = []
        previous_highest_cost = max(candidates, key=lambda t: t.get_cost()).get_cost()

        # carry forward the best solutions from the previous iteration
        for x in range(self.guaranteed_surviving_parents):
            best_individual = min(candidates, key=lambda t: t.get_cost())
            new_population.append(best_individual)
            candidates.remove(best_individual)

        # print(f"{len(candidates)} to choose from")

        if len(candidates)+self.guaranteed_surviving_parents <= self.popsize:
            return new_population + candidates

        # choose the remaining solutions randomly, with a probability proportional to the cost function
        # sorting the list based on cost would be ideal however is too expensive
        while len(new_population) < self.popsize:
            i = random.randint(0, len(candidates) - 1)
            candidate = candidates[i]

            # choose with probability (roughly) proportional to the value of the cost function
            #   - this will be incorrect if an uncalculated cost is greater than that of the previous iteration
            p = candidate.get_cost() / previous_highest_cost
            # higher cost is worse, so this gives the probability that it will fail
            if p < random.uniform(0, 1):
                new_population.append(candidates.pop(i))

        # print([p.get_cost() for p in new_population])

        return new_population

    def evaluate_all_costs(self, population):
        """Evaluates the cost function for every timetable in the given population"""
        return population

        # for i, timetable in enumerate(population):
        #     timetable: Timetable
        #     population[i].cost = timetable.get_cost()
        #
        # return population

    def choose_parents(self):
        """Chooses the best parents from the population to mate"""

        candidates = list(self.population)
        parents = []

        # choose the best parents
        for x in range(self.num_parents):
            best_parent = min(candidates, key=lambda t: t.get_cost())
            parents.append(best_parent)
            candidates.remove(best_parent)

        return parents

    def generate_offspring(self, parents):
        """Generates all the offspring"""

        offspring = []
        for x in range(self.num_offspring):
            parent1 = random.choice(parents)
            parent2 = random.choice(parents)
            child = self.crossover(parent1, parent2)
            child = child.mutate(mutate_lessons_per_day=self.mutation_amount)
            offspring.append(child)

        #offspring = self.mutate(offspring)

        return offspring

    def crossover(self, parent1, parent2):
        """Returns one offspring containing half information from each parent"""

        new_lessons = {}
        for day in range(self.days):
            new_lessons[day] = []
            added_ids = []
            potential_new_lessons = (parent1.lessons[day] + parent2.lessons[day]).copy()
            random.shuffle(potential_new_lessons)

            for x in range(len(potential_new_lessons) // 2):
                if potential_new_lessons:
                    lesson: PotentiallyScheduledLesson = potential_new_lessons.pop(0)
                    if lesson.id not in added_ids:
                        new_lessons[day].append(lesson.copy())
                        added_ids.append(lesson.id)

        timetable = Timetable(lessons=new_lessons, first_day=self.first_day, days=self.days,
                              time_per_day=self.time_per_day, seconds_per_unit_time=self.seconds_per_unit_time,
                              desired_allocations=self.desired_allocations, group_data=self.group_data,
                              day_start=self.day_start, desired_lesson_time=self.desired_lesson_time,
                              random_lesson_skip_probability=self.random_lesson_skip_probability,
                              all_students=self.all_students, unscheduled_lessons=self.unscheduled_lessons,
                              year_start=self.year_start, **self.timetable_init_kwargs)

        return timetable  # the cost function may not be needed, so it does not need to be executed here

    def mutate(self, offspring):
        """Randomly changes the offspring slightly"""

        for timetable in offspring:
            if random.uniform(0, 1) < self.mutation_chance:
                timetable.mutate()

        return offspring


class Timetable:
    """Represents a potential timetable for a given period of time"""

    def __init__(self, first_day: Optional[datetime.datetime] = None, days: int = 1, time_per_day: int = 114,
                 seconds_per_unit_time: float = 300, day_start=datetime.timedelta(hours=8, minutes=30), year_start=None,
                 unscheduled_lessons=None, group_data=None, desired_allocations=None, lessons=None,
                 desired_lesson_time=44, random_lesson_skip_probability: float = 0.2, all_students=None):
        if first_day:
            self.first_day = first_day
        else:
            self.first_day = datetime.datetime.now(datetime.timezone.utc)
        self.days = days
        self.time_per_day = time_per_day
        self.seconds_per_unit_time = seconds_per_unit_time
        self.day_start = day_start
        self.desired_lesson_time = desired_lesson_time
        self.random_lesson_skip_probability = random_lesson_skip_probability
        if desired_allocations:
            self.desired_allocations = desired_allocations
        else:
            self.desired_allocations = {}
        self.cost = float('inf')
        self.modified = True

        if year_start:
            self.year_start = year_start
        else:
            self.year_start = get_year_start()

        if unscheduled_lessons:
            self.unscheduled_lessons = []
            for lesson in unscheduled_lessons:
                self.unscheduled_lessons.append(lesson.copy())
        else:
            self.unscheduled_lessons = get_unscheduled_lessons(self.first_day, self.days, self.seconds_per_unit_time)
        random.shuffle(self.unscheduled_lessons)

        if group_data:
            self.group_data = group_data
        else:
            self.group_data = get_group_data()

        self.all_students = all_students

        if not lessons:
            self.lessons = {}  # format {day: lesson} of type {int: PotentiallyScheduledLesson}
            for d in range(self.days):
                self.lessons[d] = []
        else:
            self.lessons = lessons

    def __eq__(self, other):
        if isinstance(other, Timetable):
            return self.lessons == other.lessons
        else:
            return self == other

    def random(self, threshold=10, true_random_min=None, true_random_max=None):
        """Generates a random solution
        This algorithm makes some attempt to minimise teacher clashes while being quick to execute"""

        if true_random_min and true_random_max:
            for x in range(random.randint(true_random_min, true_random_max)):
                lesson = random.choice(self.unscheduled_lessons)
                lesson = PotentiallyScheduledLesson(lesson)
                latest_end = self.time_per_day - lesson.relative_duration
                lesson.relative_start = random.randint(0, latest_end)
                self.lessons[0].append(lesson)

        else:
            counter = 0
            for lesson in self.unscheduled_lessons:
                lesson: PotentiallyScheduledLesson
                teacher = self.get_teacher(lesson)
                day = random.randint(0, self.days - 1)
                gaps = self.get_gaps(user_id=teacher.id, days=[day], random_order=True, boundaries=True)

                for gap_start, gap in gaps:  # for each (random) gap...
                    if random.uniform(0, 1) < self.random_lesson_skip_probability:
                        continue
                    if gap > lesson.relative_duration + 1:  # if there's enough space for a lesson (need at least 1 unit either side)...
                        if gap < lesson.relative_duration * 1.5:  # if there's not much space...
                            lesson.relative_start = gap_start + 1  # schedule for start of gap (plus 1 unit break)
                            # TODO: Randomly choose between start and end
                        else:
                            latest_end = gap_start + gap - 2
                            lesson.relative_start = random.randint(gap_start,
                                                                   latest_end - lesson.relative_duration)  # allocate to random position
                        self.lessons[day].append(lesson)
                        break
                    else:
                        continue
                else:  # this triggers if the end of the loop is reached without a break statement
                    counter += 1
                    if counter > threshold:
                        break

        self.modified = True

        return self

    def get_teacher(self, lesson: 'PotentiallyScheduledLesson'):
        """Gets a teacher who teaches the given lesson
        Teachers are cached, so the cached version will be returned upon any future calls"""
        if not hasattr(lesson, 'teacher'):
            lesson.teacher = User.objects.filter(link__group_id__lesson__id__exact=lesson.id,
                                                 user_type__exact='teacher')[:1].get()
        return lesson.teacher

    def get_gaps(self, user_id, days=None, random_order=False, boundaries=False) -> List[Tuple[int, int]]:
        """Gets a list of the duration of every gap on the given day, in time units

        Days should be a list of numbers, each indicating the number of days since first_day
        By default, only gaps between lessons are returned. However, if boundaries = True, then the gaps between the
            start of the day and the first lesson will be returned (likewise with the final lesson)

        Returns dict of form [(start of gap, length of gap)] of type [(int, int)]"""
        if not days:
            days = range(self.days)

        previous = None
        gaps = []
        for day in days:
            sorted(self.lessons[day])
            if boundaries:
                previous = 0
            for lesson in self.lessons[day]:
                if previous:
                    gaps.append((previous, lesson.relative_start - previous))
                previous = lesson.relative_start
            if boundaries:
                gaps.append((previous, self.time_per_day - previous))

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

    def get_cost(self, debug=False, force=False):
        """Evaluates the cost function for the current solution"""
        POINTS_PER_TEACHER_CLASH = 100
        POINTS_PER_STUDENT_CLASH = 10
        MAX_LOAD_CONSTANT = 23  # max load = c ln c, where c is this value
        EARLY_FINISH_CONSTANT = 10
        EARLIEST_EARLY_FINISH = 48
        EVEN_ALLOCATION_CONSTANT_A = 0.4
        EVEN_ALLOCATION_CONSTANT_B = -8
        EVEN_ALLOCATION_CONSTANT_K = 1000
        WEIGHTING_OF_DIFF = 100
        VARIETY_BASE = 2
        VARIETY_COEFFICIENT = 1
        VARIETY_CONSTANT = 1_000_000
        DESIRED_LESSONS_BASE = 1.2
        DESIRED_LESSONS_MULTIPLIER = 25

        if not self.modified and not force and not debug:
            return self.cost

        total_cost = 0
        debug_info = {}
        for day in range(self.days):
            # constraints 1 & 2: clashes
            teacher_clashes = 0
            student_clashes = 0
            schedules = {}  # {user_id: [time_slot]}
            user_types = {}  # {user_id: user_type}
            for lesson in self.lessons[day]:
                for user in lesson.get_users():
                    clashes = 0
                    if user.id not in schedules:
                        schedules[user.id] = []
                    for x in range(lesson.relative_duration):
                        time_slot = lesson.relative_start + x
                        if time_slot in schedules[user.id]:
                            clashes += 1
                        else:
                            schedules[user.id].append(time_slot)
                    if user.user_type == 'teacher':
                        teacher_clashes += clashes
                    else:
                        student_clashes += clashes
                    user_types[user.id] = user.user_type
            clashes_cost = POINTS_PER_STUDENT_CLASH * student_clashes + POINTS_PER_TEACHER_CLASH * teacher_clashes

            # constraint 3: even allocation of lesson times
            def sigmoid(a):
                return 1 / (1 + math.exp(-a))

            weighting = sigmoid(
                EVEN_ALLOCATION_CONSTANT_B + EVEN_ALLOCATION_CONSTANT_A * (self.first_day - self.year_start).days)
            diffs = 0
            for group_id in self.group_data:
                diff = abs(self.group_data[group_id][0] - self.desired_allocations[group_id]) / \
                       self.desired_allocations[group_id]
                diffs += diff
            even_allocation_cost = WEIGHTING_OF_DIFF * weighting * diffs / EVEN_ALLOCATION_CONSTANT_K

            # constraint 3a: how many lessons
            total_lesson_time = 0
            n_students = 0
            if not self.all_students:
                for user_id in schedules:
                    if user_types[user_id] == 'student':
                        total_lesson_time += len(schedules[user_id])
                        n_students += 1
            else:
                for student in self.all_students:
                    if student.id in schedules:
                        total_lesson_time += len(schedules[student.id])
                    n_students += 1
            try:
                average_lesson_time = total_lesson_time / n_students
            except ZeroDivisionError:
                average_lesson_time = 0
            lessons_scheduled_cost = DESIRED_LESSONS_MULTIPLIER * DESIRED_LESSONS_BASE ** (self.desired_lesson_time - average_lesson_time)

            # NOTE: constraint 4 is being computed with constraint 7

            # constraint 5: variety of subjects
            variety_cost = 0
            for group_id in self.group_data:
                variety_cost += VARIETY_COEFFICIENT * (VARIETY_BASE ** self.group_data[group_id][1])
            variety_cost /= VARIETY_CONSTANT * len(self.group_data)

            # constraint 6: max daily workload
            daily_workload_cost = 0
            for user_id in schedules:
                # NOTE: It is assumed that if any clashes occur, the user will miss out on
                # all but one of the concurrent events, so it does not contribute to their overall workload
                daily_workload_cost += max(math.exp(len(schedules[user_id]) / MAX_LOAD_CONSTANT) - MAX_LOAD_CONSTANT, 0)

            # constraint 7: gaps
            gaps_cost = 0
            for user_id in schedules:  # NOTE: schedules is only used for a list of user ids
                gaps = self.get_gaps(user_id)
                for gap in gaps:
                    gaps_cost += self.get_gap_cost(gap)

            # constraint 8: early finish time
            early_finish_cost = 0
            for user_id in schedules:
                finish_time = max(schedules[user_id]) - EARLIEST_EARLY_FINISH
                if finish_time > 0:
                    early_finish_cost += finish_time / EARLY_FINISH_CONSTANT

            total_cost += clashes_cost + even_allocation_cost + lessons_scheduled_cost + variety_cost \
                          + daily_workload_cost + gaps_cost + early_finish_cost

            debug_info = {
                'teacher clashes': teacher_clashes,
                'student clashes': student_clashes,
                'clashes cost': clashes_cost,
                'total diffs': diffs,
                'even allocation cost': even_allocation_cost,
                'average lesson time': average_lesson_time,
                'lessons scheduled cost': lessons_scheduled_cost,
                'variety cost': variety_cost,
                'daily workload cost': daily_workload_cost,
                'gaps cost': gaps_cost,
                'early finish cost': early_finish_cost
            }

            # print(debug_info)

        self.cost = total_cost
        self.modified = False

        if debug:
            return debug_info
        else:
            return max(total_cost, 0)

    def get_fitness(self):
        """Returns the fitness value for a solution
        This is simply the negative of the cost value"""
        return -self.get_cost()

    def mutate(self, mutate_lessons_per_day=2):
        """Mutates the given solution (for use in a genetic algorithm)
        NOTE: The same lesson could be mutated twice (although unlikely)"""

        for day in range(self.days):
            for x in range(mutate_lessons_per_day):
                n = random.randint(1, 3)
                if n == 1:
                    # mutate start time of random lesson
                    if self.lessons[day]:
                        i = random.randint(0, len(self.lessons[day]) - 1)
                        lesson = self.lessons[day][i]
                        latest_time = self.time_per_day - lesson.relative_duration
                        lesson.relative_start = random.randint(0, latest_time)
                elif n == 2:
                    # delete a random lesson
                    if self.lessons[day]:
                        lesson = self.lessons[day].pop(random.randint(0, len(self.lessons[day]) - 1))
                        # add to random position in unscheduled lessons
                        self.unscheduled_lessons.insert(random.randint(0, len(self.unscheduled_lessons)), lesson)
                elif n == 3:
                    # add a random lesson
                    if self.unscheduled_lessons:
                        lesson = self.unscheduled_lessons.pop(random.randint(0, len(self.unscheduled_lessons) - 1))
                        latest_time = self.time_per_day - lesson.relative_duration
                        lesson.relative_start = random.randint(0, latest_time)
                        self.lessons[day].append(lesson)

        self.modified = True

        return self

    def add(self):
        """Update the database to include the start times for all lessons currently stored within this object"""
        for day in self.lessons:
            for lesson in self.lessons[day]:
                new_lesson = Lesson()
                new_lesson.group_id = lesson.group_id
                new_lesson.duration = lesson.duration  # relative_duration not required because duration is never modified
                new_lesson.topic = lesson.topic
                new_lesson.fixed = True
                start_time = self.first_day + datetime.timedelta(days=day) + self.day_start + datetime.timedelta(seconds=lesson.relative_start * self.seconds_per_unit_time)
                new_lesson.start = start_time
                new_lesson.save()


class PotentiallyScheduledLesson:
    """A Lesson used as part of a Timetable
    Notably, this abstracts the start time to make computation easier"""

    DESIRED_FIELDS = [
        'id',
        'duration',
        'group_id',
        'topic'
    ]

    def __init__(self, lesson, seconds_per_time_unit: float = 300):
        for field in self.DESIRED_FIELDS:
            self.__dict__[field] = lesson.__dict__[field]
        self.relative_start = None  # contains start time in time units relative to start of day
        self.relative_duration = math.floor(lesson.duration.total_seconds() / seconds_per_time_unit)
        self.users = None

    def __gt__(self, other):
        return self.relative_start > other

    def __lt__(self, other):
        return self.relative_start < other

    def __str__(self):
        if hasattr(self, 'teacher'):
            return f"<Lesson teacher='{self.teacher.username}' start={self.relative_start}>"
        else:
            return f"<Lesson start={self.relative_start}>"

    def copy(self):
        return copy.copy(self)

    def __repr__(self):
        return self.__str__()

    def get_users(self):
        """Retrieves all users in this lesson, caching the result for subsequent queries"""
        if not self.users:
            self.users = User.objects.filter(link__group_id__lesson__id__exact=self.id)
        return self.users

    @classmethod
    def from_lesson(cls, *args, **kwargs):
        """DEPRECATED: Should not be used"""
        return cls(*args, **kwargs)
