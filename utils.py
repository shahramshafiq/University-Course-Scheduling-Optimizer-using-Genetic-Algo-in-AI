# utils.py
# small helper functions: loading data, checking constraints, and misc tools

import json
import copy
import random


# Data Loading
def load_courses(path='course_catalog.json'):
    with open(path, 'r') as f:
        data = json.load(f)
    return data['courses']


def load_students(path='student_requirements.json'):
    with open(path, 'r') as f:
        data = json.load(f)
    return data['students'], data['friend_pairs'], data['global_constraints']


def load_config(path='config.yaml'):
    """load config from yaml if possible, else use defaults"""
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        return _default_config()


def _default_config():
    """basic fallback config when yaml is not available"""
    return {
        'population': {
            'size': 60,
            'initialization_strategy': {
                'random_valid': 0.40,
                'greedy_time': 0.40,
                'greedy_friend': 0.20
            },
            'elitism': {'enabled': True, 'rate': 0.10}
        },
        'selection': {
            'tournament': {'enabled': True, 'rate': 0.70, 'tournament_size': 5},
            'roulette': {'enabled': True, 'rate': 0.30}
        },
        'crossover': {
            'probability': 0.80,
            'operators': {
                'single_point': {'enabled': True, 'weight': 0.35},
                'uniform': {'enabled': True, 'weight': 0.35},
                'course_based': {'enabled': True, 'weight': 0.30}
            },
            'repair': {'max_attempts': 10}
        },
        'mutation': {
            'base_rates': {
                'section_change': 0.12,
                'course_swap': 0.10,
                'time_shift': 0.08,
                'friend_align': 0.15
            },
            'adaptive': {
                'enabled': True,
                'diversity_threshold': 0.30,
                'rate_multiplier': 1.5,
                'check_interval': 10
            }
        },
        'fitness': {
            'weights': {
                'time_preference': 0.30,
                'gap_minimization': 0.25,
                'friend_satisfaction': 0.20,
                'workload_balance': 0.15,
                'lunch_break': 0.10
            },
            'penalties': {
                'hard_constraint': -1000,
                'time_conflict': -1000,
                'missing_credits': -800,
                'too_many_courses': -500,
                'blocked_time': -1000
            }
        },
        'diversity': {
            'maintenance': {
                'enabled': True,
                'check_interval': 10,
                'low_threshold': 0.30,
                'injection_rate': 0.20
            }
        },
        'logging': {
            'console': {'frequency': 10}
        },
        'termination': {
            'max_generations': 300,
            'convergence': {
                'enabled': True,
                'patience': 40,
                'improvement_threshold': 0.001
            },
            'similarity': {
                'enabled': True,
                'threshold': 0.85,
                'tolerance': 0.02
            }
        }
    }


# Course / Section Helpers
def get_section(courses, course_id, section_id):
    """return the whole section dict for this course and section id"""
    for sec in courses[course_id]['sections']:
        if sec['section_id'] == section_id:
            return sec
    return None


def get_section_schedule(courses, course_id, section_id):
    """return list of day/time dicts for one section"""
    sec = get_section(courses, course_id, section_id)
    if sec is None:
        return []
    return sec['schedule']


def all_sections_for(courses, course_id):
    """get list of all section ids for a course"""
    ids = []
    for s in courses[course_id]['sections']:
        ids.append(s['section_id'])
    return ids


def get_days_times(courses, course_id, section_id):
    """return list of (day, time) for this section"""
    sched = get_section_schedule(courses, course_id, section_id)
    pairs = []
    for e in sched:
        pairs.append((e['day'], e['time']))
    return pairs


# Constraint Checking
def has_time_conflict(schedule_a, schedule_b):
    """true if any (day,time) pair overlaps between two schedules"""
    set_a = set()
    for e in schedule_a:
        set_a.add((e['day'], e['time']))

    set_b = set()
    for e in schedule_b:
        set_b.add((e['day'], e['time']))

    return len(set_a.intersection(set_b)) > 0


def violates_blocked_time(schedule, blocked_slots):
    """true if schedule uses a blocked (day,time) pair"""
    for slot in schedule:
        for blocked in blocked_slots:
            if slot['day'] == blocked['day'] and slot['time'] == blocked['time']:
                return True
    return False


def prerequisites_satisfied(course_id, courses, completed):
    """check if all prereqs for a course are already completed"""
    prereqs = courses[course_id].get('prerequisites', [])
    for p in prereqs:
        if p not in completed:
            return False
    return True


def courses_per_day(student_courses, courses):
    """count how many meetings a student has per day"""
    day_counts = {}
    for entry in student_courses:
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        for slot in sched:
            day = slot['day']
            if day in day_counts:
                day_counts[day] += 1
            else:
                day_counts[day] = 1
    return day_counts


def max_courses_per_day(student_courses, courses):
    """largest number of meetings in a single day"""
    counts = courses_per_day(student_courses, courses)
    if not counts:
        return 0
    return max(counts.values())


# Student Course List Builder
def build_required_courses(student_id, students, chosen_electives=None):
    """build list of all course ids a student should take"""
    s = students[student_id]
    core = []
    for c in s['required_courses']['core']:
        core.append(c)

    n_elec = s['required_courses']['electives']
    pool = s['required_courses']['elective_pool']

    if chosen_electives is not None and student_id in chosen_electives:
        electives = chosen_electives[student_id]
    else:
        if pool and n_elec > 0:
            # pick some electives from the pool
            count = n_elec
            if n_elec > len(pool):
                count = len(pool)
            electives = random.sample(pool, count)
        else:
            electives = []

    result = []
    for c in core:
        result.append(c)
    for e in electives:
        result.append(e)
    return result


def total_credits(course_ids, courses):
    """sum of credits for all given course ids"""
    total = 0
    for c in course_ids:
        total += courses[c]['credits']
    return total


# Validation
def validate_student_schedule(student_id, student_courses, students, courses):
    """check one student's schedule against all hard rules"""
    violations = []
    s = students[student_id]
    completed = set(s['completed_courses'])
    blocked = s['time_preferences']['blocked']['slots']

    course_ids = []
    for e in student_courses:
        course_ids.append(e['course_id'])

    credits = total_credits(course_ids, courses)
    if credits != s['required_credits']:
        violations.append(
            f"{student_id}: credits={credits} expected={s['required_credits']}"
        )

    i = 0
    while i < len(student_courses):
        j = i + 1
        while j < len(student_courses):
            si = get_section_schedule(
                courses,
                student_courses[i]['course_id'],
                student_courses[i]['section_id']
            )
            sj = get_section_schedule(
                courses,
                student_courses[j]['course_id'],
                student_courses[j]['section_id']
            )
            if has_time_conflict(si, sj):
                cid_i = student_courses[i]['course_id']
                cid_j = student_courses[j]['course_id']
                violations.append(
                    f"{student_id}: time conflict {cid_i} vs {cid_j}"
                )
            j += 1
        i += 1

    for entry in student_courses:
        cid = entry['course_id']
        if not prerequisites_satisfied(cid, courses, completed):
            violations.append(f"{student_id}: prereq not met for {cid}")

    if max_courses_per_day(student_courses, courses) > s['max_courses_per_day']:
        violations.append(
            f"{student_id}: more than {s['max_courses_per_day']} courses/day"
        )

    for entry in student_courses:
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        if violates_blocked_time(sched, blocked):
            violations.append(
                f"{student_id}: blocked-time violation in {entry['course_id']}"
            )

    return violations


def validate_chromosome(chromosome, students, courses):
    """run validate_student_schedule for all students"""
    all_violations = []
    for sid, student_courses in chromosome.items():
        all_violations += validate_student_schedule(sid, student_courses, students, courses)
    return all_violations


# Diversity Metric
def chromosome_signature(chromosome):
    """compact representation of chromosome (for diversity check)"""
    parts = []
    for sid in sorted(chromosome.keys()):
        entries = chromosome[sid]
        sorted_entries = sorted(entries, key=lambda e: e['course_id'])
        for entry in sorted_entries:
            parts.append((sid, entry['course_id'], entry['section_id']))
    return tuple(parts)


def population_diversity(population):
    """fraction of unique chromosomes in population"""
    if not population:
        return 0.0

    sigs = set()
    for ind in population:
        sigs.add(chromosome_signature(ind['chromosome']))

    return len(sigs) / len(population)


# Pretty-print helpers
DAYS_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
TIME_LABELS = {
    8: '8AM', 9: '9AM', 10: '10AM', 11: '11AM', 12: '12PM',
    13: '1PM', 14: '2PM', 15: '3PM', 16: '4PM', 17: '5PM'
}


def format_time(t):
    """turn integer hour into label like '2PM'"""
    if t in TIME_LABELS:
        return TIME_LABELS[t]
    return f'{t}:00'


def deep_copy_chromosome(chromosome):
    """just a thin wrapper around deepcopy for chromosomes"""
    return copy.deepcopy(chromosome)