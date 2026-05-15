# operators.py
# this file defines crossover + mutation operators and some repair helpers

import random
import copy

from utils import (
    get_section_schedule, all_sections_for, has_time_conflict,
    violates_blocked_time, prerequisites_satisfied, total_credits
)
from chromosome import make_entry, pick_valid_section


# simple helper to check if two entries conflict
def _entries_conflict(courses, entry_a, entry_b):
    sched_a = get_section_schedule(courses, entry_a['course_id'], entry_a['section_id'])
    sched_b = get_section_schedule(courses, entry_b['course_id'], entry_b['section_id'])
    return has_time_conflict(sched_a, sched_b)

# Repair Function
def repair_student_schedule(student_id, entries, students, courses, max_attempts=10):
    """try to fix a single student's schedule by changing sections"""
    s = students[student_id]
    blocked = s['time_preferences']['blocked']['slots']
    completed = set(s['completed_courses'])

    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        changed = False

        i = 0
        while i < len(entries):
            entry = entries[i]
            cid = entry['course_id']
            sched = get_section_schedule(courses, cid, entry['section_id'])

            blocked_violation = violates_blocked_time(sched, blocked)

            conflict = False
            j = 0
            while j < len(entries):
                if i != j:
                    other_sched = get_section_schedule(
                        courses,
                        entries[j]['course_id'],
                        entries[j]['section_id']
                    )
                    if has_time_conflict(sched, other_sched):
                        conflict = True
                        break
                j += 1

            if blocked_violation or conflict:
                other_entries = []
                k = 0
                while k < len(entries):
                    if k != i:
                        other_entries.append(entries[k])
                    k += 1

                new_entry = pick_valid_section(
                    cid,
                    courses,
                    s,
                    other_entries,
                    max_attempts=max_attempts
                )
                if new_entry:
                    entries[i] = new_entry
                    changed = True
                    break  # restart scan
            i += 1

        if not changed:
            break

    return entries


def repair_chromosome(chromosome, students, courses, max_attempts=10):
    """run repair on every student in the chromosome"""
    for sid in chromosome:
        chromosome[sid] = repair_student_schedule(
            sid, chromosome[sid], students, courses, max_attempts
        )
    return chromosome

# Crossover Operator A – Single-Point
def crossover_single_point(parent1_chrom, parent2_chrom, students, courses, max_attempts=10):
    """one cut across student list and swap tails"""
    student_ids = list(students.keys())
    cut = random.randint(1, len(student_ids) - 1)

    child1 = {}
    child2 = {}

    i = 0
    while i < len(student_ids):
        sid = student_ids[i]
        if i < cut:
            child1[sid] = copy.deepcopy(parent1_chrom[sid])
            child2[sid] = copy.deepcopy(parent2_chrom[sid])
        else:
            child1[sid] = copy.deepcopy(parent2_chrom[sid])
            child2[sid] = copy.deepcopy(parent1_chrom[sid])
        i += 1

    child1 = repair_chromosome(child1, students, courses, max_attempts)
    child2 = repair_chromosome(child2, students, courses, max_attempts)
    return child1, child2

# Crossover Operator B – Uniform
def crossover_uniform(parent1_chrom, parent2_chrom, students, courses, max_attempts=10):
    """for each student pick schedule from parent1 or parent2 randomly"""
    child1 = {}
    child2 = {}

    for sid in students.keys():
        r = random.random()
        if r < 0.5:
            child1[sid] = copy.deepcopy(parent1_chrom[sid])
            child2[sid] = copy.deepcopy(parent2_chrom[sid])
        else:
            child1[sid] = copy.deepcopy(parent2_chrom[sid])
            child2[sid] = copy.deepcopy(parent1_chrom[sid])

    child1 = repair_chromosome(child1, students, courses, max_attempts)
    child2 = repair_chromosome(child2, students, courses, max_attempts)
    return child1, child2

# Crossover Operator C – Course-Based
def crossover_course_based(parent1_chrom, parent2_chrom, students, courses, max_attempts=10):
    """swap section choices for some common courses between parents"""
    child1 = copy.deepcopy(parent1_chrom)
    child2 = copy.deepcopy(parent2_chrom)

    for sid in students.keys():
        entries1 = child1[sid]
        entries2 = child2[sid]

        lookup1 = {}
        i = 0
        while i < len(entries1):
            e = entries1[i]
            lookup1[e['course_id']] = i
            i += 1

        lookup2 = {}
        j = 0
        while j < len(entries2):
            e = entries2[j]
            lookup2[e['course_id']] = j
            j += 1

        common = list(set(lookup1.keys()) & set(lookup2.keys()))
        if not common:
            continue

        half = len(common) // 2
        if half < 1:
            half = 1
        n_swap = random.randint(1, half)
        to_swap = random.sample(common, n_swap)

        for cid in to_swap:
            i1 = lookup1[cid]
            i2 = lookup2[cid]
            sec1 = entries1[i1]['section_id']
            sec2 = entries2[i2]['section_id']
            entries1[i1] = make_entry(cid, sec2, courses)
            entries2[i2] = make_entry(cid, sec1, courses)

    child1 = repair_chromosome(child1, students, courses, max_attempts)
    child2 = repair_chromosome(child2, students, courses, max_attempts)
    return child1, child2

# Crossover Dispatcher
def _pick_crossover_operator(weights):
    """pick an index based on weights list"""
    total = 0.0
    i = 0
    while i < len(weights):
        total += weights[i]
        i += 1

    r = random.uniform(0, total)
    cumul = 0.0
    idx = 0

    j = 0
    while j < len(weights):
        cumul += weights[j]
        if r <= cumul:
            idx = j
            break
        j += 1

    return idx


def crossover(parent1, parent2, students, courses, config):
    """apply one of 3 crossover operators based on config weights"""
    if random.random() > config['crossover']['probability']:
        return (copy.deepcopy(parent1['chromosome']),
                copy.deepcopy(parent2['chromosome']))

    ops = config['crossover']['operators']
    weights = [
        ops['single_point']['weight'],
        ops['uniform']['weight'],
        ops['course_based']['weight'],
    ]

    op = _pick_crossover_operator(weights)

    p1c = parent1['chromosome']
    p2c = parent2['chromosome']
    max_att = config['crossover']['repair']['max_attempts']

    if op == 0:
        return crossover_single_point(p1c, p2c, students, courses, max_att)
    elif op == 1:
        return crossover_uniform(p1c, p2c, students, courses, max_att)
    else:
        return crossover_course_based(p1c, p2c, students, courses, max_att)

# Mutation Operator 1 – Section Change
def mutate_section_change(chromosome, students, courses, rates):
    """pick another valid section for a random course"""
    rate = rates.get('section_change', 0.12)
    chromosome = copy.deepcopy(chromosome)

    for sid in students.keys():
        if random.random() > rate:
            continue

        entries = chromosome[sid]
        if not entries:
            continue

        idx = random.randint(0, len(entries) - 1)
        cid = entries[idx]['course_id']
        current_sec = entries[idx]['section_id']

        sections = all_sections_for(courses, cid)
        others = []
        i = 0
        while i < len(sections):
            s_val = sections[i]
            if s_val != current_sec:
                others.append(s_val)
            i += 1

        if not others:
            continue

        new_sec = random.choice(others)
        entries[idx] = make_entry(cid, new_sec, courses)
        chromosome[sid] = repair_student_schedule(sid, entries, students, courses)

    return chromosome

# Mutation Operator 2 – Course Swap (swap sections of two courses)
def mutate_course_swap(chromosome, students, courses, rates):
    """swap section assignments of two courses in one student's schedule"""
    rate = rates.get('course_swap', 0.10)
    chromosome = copy.deepcopy(chromosome)

    for sid in students.keys():
        if random.random() > rate:
            continue

        entries = chromosome[sid]
        if len(entries) < 2:
            continue

        i, j = random.sample(range(len(entries)), 2)
        cid_i = entries[i]['course_id']
        cid_j = entries[j]['course_id']
        sec_i = entries[i]['section_id']
        sec_j = entries[j]['section_id']

        secs_i = all_sections_for(courses, cid_i)
        secs_j = all_sections_for(courses, cid_j)

        if sec_j in secs_i:
            entries[i] = make_entry(cid_i, sec_j, courses)
        if sec_i in secs_j:
            entries[j] = make_entry(cid_j, sec_i, courses)

        chromosome[sid] = repair_student_schedule(sid, entries, students, courses)

    return chromosome

# Mutation Operator 3 – Time Slot Shift (change to different-time section)
def mutate_time_shift(chromosome, students, courses, rates):
    """move a course to a section that meets at different times"""
    rate = rates.get('time_shift', 0.08)
    chromosome = copy.deepcopy(chromosome)

    for sid in students.keys():
        if random.random() > rate:
            continue

        s = students[sid]
        entries = chromosome[sid]
        if not entries:
            continue

        idx = random.randint(0, len(entries) - 1)
        cid = entries[idx]['course_id']
        current_sec = entries[idx]['section_id']

        current_times = set()
        for d, t in entries[idx]['days_times']:
            current_times.add(t)

        sections = all_sections_for(courses, cid)
        candidates = []

        i = 0
        while i < len(sections):
            sec = sections[i]
            if sec != current_sec:
                new_times = set()
                sched = get_section_schedule(courses, cid, sec)
                j = 0
                while j < len(sched):
                    new_times.add(sched[j]['time'])
                    j += 1
                if new_times != current_times:
                    candidates.append(sec)
            i += 1

        if not candidates:
            continue

        new_sec = random.choice(candidates)
        entries[idx] = make_entry(cid, new_sec, courses)
        chromosome[sid] = repair_student_schedule(sid, entries, students, courses)

    return chromosome

# Mutation Operator 4 – Friend Alignment
def mutate_friend_align(chromosome, students, courses, rates, friend_pairs):
    """try to align sections for a random friend pair"""
    rate = rates.get('friend_align', 0.15)
    chromosome = copy.deepcopy(chromosome)

    if random.random() > rate:
        return chromosome

    pair = random.choice(friend_pairs)
    sid_a = pair[0]
    sid_b = pair[1]

    if sid_a not in chromosome or sid_b not in chromosome:
        return chromosome

    entries_a = chromosome[sid_a]
    entries_b = chromosome[sid_b]

    courses_a = {}
    for e in entries_a:
        courses_a[e['course_id']] = e['section_id']

    courses_b = {}
    for e in entries_b:
        courses_b[e['course_id']] = e['section_id']

    common = set(courses_a.keys()) & set(courses_b.keys())
    if not common:
        return chromosome

    cid = random.choice(list(common))
    sec_a = courses_a[cid]
    sec_b = courses_b[cid]

    if sec_a == sec_b:
        return chromosome

    i = 0
    while i < len(entries_b):
        entry = entries_b[i]
        if entry['course_id'] == cid:
            new_entry = make_entry(cid, sec_a, courses)
            entries_b[i] = new_entry
            break
        i += 1

    chromosome[sid_b] = repair_student_schedule(sid_b, entries_b, students, courses)
    return chromosome

# Mutation Dispatcher
def mutate(individual, students, courses, config, friend_pairs, current_rates=None):
    """run all mutation operators on an individual"""
    if current_rates is None:
        current_rates = config['mutation']['base_rates']

    chrom = individual['chromosome']
    chrom = mutate_section_change(chrom, students, courses, current_rates)
    chrom = mutate_course_swap(chrom, students, courses, current_rates)
    chrom = mutate_time_shift(chrom, students, courses, current_rates)
    chrom = mutate_friend_align(chrom, students, courses, current_rates, friend_pairs)

    return {'chromosome': chrom, 'fitness': None}

# Adaptive Mutation Rate Manager
def get_adaptive_rates(base_rates, diversity, config):
    """adjust mutation rates based on population diversity"""
    threshold = config['mutation']['adaptive']['diversity_threshold']
    multiplier = config['mutation']['adaptive']['rate_multiplier']

    if diversity < threshold:
        new_rates = {}
        for k, v in base_rates.items():
            boosted = v * multiplier
            if boosted > 1.0:
                boosted = 1.0
            new_rates[k] = boosted
        return new_rates

    return dict(base_rates)