# selection.py
# selection helpers: tournament, roulette, elitism, and diversity injection

import random
import copy


# Tournament Selection
def tournament_selection(population, tournament_size=5):
    """pick the best out of a small random group"""
    size = tournament_size
    if tournament_size > len(population):
        size = len(population)

    candidates = random.sample(population, size)
    best = candidates[0]
    i = 1
    while i < len(candidates):
        if candidates[i]['fitness'] > best['fitness']:
            best = candidates[i]
        i += 1
    return best


# Roulette Wheel Selection
def roulette_wheel_selection(population):
    """fitness-proportionate selection (handles negative by shifting)"""
    fitnesses = []
    for ind in population:
        fitnesses.append(ind['fitness'])

    min_fit = min(fitnesses)

    shifted = []
    i = 0
    while i < len(fitnesses):
        shifted.append(fitnesses[i] - min_fit)
        i += 1

    total = sum(shifted)

    if total == 0:
        return random.choice(population)

    pick = random.uniform(0, total)
    cumulative = 0.0

    j = 0
    while j < len(population):
        cumulative += shifted[j]
        if cumulative >= pick:
            return population[j]
        j += 1

    return population[-1]


# Combined Selection (tournament / roulette mix)
def select_parent(population, config):
    """choose one parent using tournament or roulette based on config"""
    t_rate = config['selection']['tournament']['rate']
    t_size = config['selection']['tournament']['tournament_size']

    r = random.random()
    if r < t_rate:
        return tournament_selection(population, t_size)
    else:
        return roulette_wheel_selection(population)


def select_parents(population, config):
    """select two (ideally) different parents"""
    p1 = select_parent(population, config)
    p2 = select_parent(population, config)

    attempts = 0
    while p2 is p1 and attempts < 10:
        p2 = select_parent(population, config)
        attempts += 1

    return p1, p2


# Elitism
def apply_elitism(old_population, new_population, config):
    """copy the best individuals from old_population into new_population"""
    if not config['population']['elitism']['enabled']:
        return new_population

    rate = config['population']['elitism']['rate']
    n_keep = int(len(old_population) * rate)
    if n_keep < 1:
        n_keep = 1

    elites = sorted(
        old_population,
        key=lambda i: i['fitness'],
        reverse=True
    )[:n_keep]

    new_population.sort(key=lambda i: i['fitness'])

    k = 0
    while k < len(elites) and k < len(new_population):
        new_population[k] = copy.deepcopy(elites[k])
        k += 1

    return new_population


# Diversity-based injection
def inject_random_individuals(population, n_inject, students, courses, config):
    """replace a few worst individuals with new random ones"""
    from chromosome import init_random_valid

    population.sort(key=lambda ind: ind['fitness'])

    limit = n_inject
    if n_inject > len(population):
        limit = len(population)

    i = 0
    while i < limit:
        new_chrom = {}
        for sid in students.keys():
            new_chrom[sid] = init_random_valid(sid, students, courses)
        population[i] = {'chromosome': new_chrom, 'fitness': None}
        i += 1

    return population