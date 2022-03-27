import datetime
import random
from typing import List, Sequence

from src.django_project.timetable.models import Lesson, User


def should_stop(current_population, previous_population, iterations):
    if iterations > 1000:
        return True
    else:
        return False


class Population:
    """Represents a population of timetables for use in the genetic algorithm"""

    def __init__(self, timetable_init_kwargs, popsize=100, num_parents=50, guaranteed_parent_survival=5, stopping_condition=should_stop):
        """

        :param popsize: The population size
        :param stopping_condition: A function taking in:
         - the current population (of type Population)
         - previous population (THIS WILL BE NONE ON THE FIRST ITERATION)
         - the number of iterations / generations
         and returning True to stop and False to continue
        """

        self.popsize = popsize
        self.num_parents = num_parents
        self.guaranteed_surviving_parents = guaranteed_parent_survival
        self.stopping_condition = stopping_condition
        self.generations = 0

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
        while not self.stopping_condition(self, previous, self.generations):
            previous = self.copy()
            self.iterate()
            self.generations += 1

    def iterate(self):
        """Performs one iteration of the genetic algorithm on the current population"""

        self.population = self.evaluate_all_costs(self.population)
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
        # TODO
        return Timetable(), float('inf')

    def mutate(self, offspring):
        """Changes the offspring slightly"""
        # TODO
        return offspring

    def copy(self):
        """Returns an identical copy of the object"""
        # TODO
        return self


class Timetable:
    """Represents a potential timetable for a given period of time"""

    def __init__(self, days: int = 1, time_per_day: int = 114, seconds_per_unit_time: float = 300, day_start=datetime.time(8, 30, 0), unscheduled_lessons=None):
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

        self.lessons = []

    def random(self):
        """Generates a completely random solution
        All solutions should be equally likely, EXCEPT those involving clashes
        This algorithm makes some attempt to minimise clashes while being quick to execute"""

        # for each (randomly ordered) teacher...
        for teacher in User.objects.filter(user_type__exact='teacher').order_by('?'):
            # for each (randomly ordered) lesson that involves this teacher
            for lesson in Lesson.objects.filter(group_id__link__user_id__id__exact=teacher.id).order_by('?').order_by('added'):
                # try to schedule at random time
                # if no time available to schedule, break
                pass

        return self

    def cost(self):
        """Evaluates the cost function for the given solution"""
        return 1

    def mutate(self):
        """Mutates the given solution (for use in a genetic algorithm)"""
        return self

    def add(self):
        """Adds all lessons contained within this timetable into the database"""
