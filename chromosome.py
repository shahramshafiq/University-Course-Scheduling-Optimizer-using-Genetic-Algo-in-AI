import random
import copy

from utils import (
    get_section_schedule, get_days_times, all_sections_for,
    build_required_courses, total_credits, prerequisites_satisfied,
    has_time_conflict, violates_blocked_time, max_courses_per_day,
    deep_copy_chromosome
)


# builds a single course entry with its schedule
def make_entry(course_id, section_id, courses):
    days_times = get_days_times(courses, course_id, section_id)
    return {
        'course_id':  course_id,
        'section_id': section_id,
        'days_times': days_times
    }


# returns flat list of (day, time, course_id) for a student's schedule
def decode_schedule(student_courses):
    slots = []
    for entry in student_courses:
        for (day, time) in entry['days_times']:
            slots.append((day, time, entry['course_id']))
    return slots


# returns a set of (day, time) slots the student is busy at
def schedule_as_set(student_courses):
    busy = set()
    for entry in student_courses:
        for (day, time) in entry['days_times']:
            busy.add((day, time))
    return busy


# gives a preference score to a section based on student's preferred times
def get_preference_score(sec_id, course_id, courses, preferred_times):
    if not preferred_times:
        return 0
    sched = get_section_schedule(courses, course_id, sec_id)
    score = 0
    for slot in sched:
        if slot['time'] in preferred_times:
            score += 1
    return score


# tries to find a valid section for a course that doesn't conflict with existing schedule
def pick_valid_section(course_id, courses, student_data, existing_entries,
                        preferred_times=None, max_attempts=15):
    blocked  = student_data['time_preferences']['blocked']['slots']
    sections = all_sections_for(courses, course_id)

    # collect all currently occupied (day, time) slots
    occupied = set()
    for e in existing_entries:
        for (d, t) in e['days_times']:
            occupied.add((d, t))

    # sort sections by preference score then shuffle to break ties
    ordered = sorted(sections, key=lambda s: get_preference_score(s, course_id, courses, preferred_times), reverse=True)
    random.shuffle(ordered)

    for _ in range(max_attempts):
        for sec_id in ordered:
            sched = get_section_schedule(courses, course_id, sec_id)

            # skip if this section is during a blocked time
            if violates_blocked_time(sched, blocked):
                continue

            # skip if this section clashes with something already scheduled
            new_slots = set()
            for sl in sched:
                new_slots.add((sl['day'], sl['time']))

            if new_slots & occupied:
                continue

            return make_entry(course_id, sec_id, courses)

    # fallback: just return any section that isn't blocked
    for sec_id in sections:
        sched = get_section_schedule(courses, course_id, sec_id)
        if not violates_blocked_time(sched, blocked):
            return make_entry(course_id, sec_id, courses)

    # last resort: return the first section no matter what
    return make_entry(course_id, sections[0], courses)


# picks electives randomly from the student's elective pool
def _select_electives(student_id, students, elective_pool_override=None):
    s = students[student_id]
    n = s['required_courses']['electives']
    pool = elective_pool_override or s['required_courses']['elective_pool']
    if n == 0 or not pool:
        return []
    return random.sample(pool, min(n, len(pool)))


# strategy 1: assign random sections, just avoid blocked times
def init_random_valid(student_id, students, courses, elective_override=None):
    s = students[student_id]
    completed = set(s['completed_courses'])
    electives = _select_electives(student_id, students, elective_override)
    course_list = list(s['required_courses']['core']) + electives

    entries = []
    for cid in course_list:
        if not prerequisites_satisfied(cid, courses, completed):
            continue
        entry = pick_valid_section(cid, courses, s, entries)
        if entry:
            entries.append(entry)

    return entries


# strategy 2: prefer sections that match the student's preferred time slots
def init_greedy_time(student_id, students, courses, elective_override=None):
    s = students[student_id]
    completed = set(s['completed_courses'])
    preferred = s['time_preferences']['preferred']['time_slots']
    electives = _select_electives(student_id, students, elective_override)
    course_list = list(s['required_courses']['core']) + electives

    entries = []
    for cid in course_list:
        if not prerequisites_satisfied(cid, courses, completed):
            continue
        entry = pick_valid_section(cid, courses, s, entries, preferred_times=preferred)
        if entry:
            entries.append(entry)

    return entries


# strategy 3: try to match the same section a friend is already in
def init_greedy_friend(student_id, students, courses, friend_schedules=None,
                        elective_override=None):
    s = students[student_id]
    completed = set(s['completed_courses'])
    friends = s['friends']
    electives = _select_electives(student_id, students, elective_override)
    course_list = list(s['required_courses']['core']) + electives

    # collect all (course, section) pairs that friends are enrolled in
    friend_sections = set()
    if friend_schedules:
        for fid in friends:
            if fid in friend_schedules:
                for entry in friend_schedules[fid]:
                    friend_sections.add((entry['course_id'], entry['section_id']))

    entries = []
    for cid in course_list:
        if not prerequisites_satisfied(cid, courses, completed):
            continue

        # build the set of times already used by this student
        used = set()
        for e in entries:
            for (d, t) in e['days_times']:
                used.add((d, t))

        blocked = s['time_preferences']['blocked']['slots']
        chosen = None

        # check if a friend is in this course and grab their section if possible
        for (fc, fs) in friend_sections:
            if fc == cid:
                sched = get_section_schedule(courses, cid, fs)
                if violates_blocked_time(sched, blocked):
                    continue
                slots = set()
                for sl in sched:
                    slots.add((sl['day'], sl['time']))
                if not (slots & used):
                    chosen = make_entry(cid, fs, courses)
                    break

        # if no friend section worked, just pick any valid one
        if chosen is None:
            chosen = pick_valid_section(cid, courses, s, entries)

        if chosen:
            entries.append(chosen)

    return entries


# creates the full starting population using all 3 strategies
def initialise_population(pop_size, students, courses, config):
    strat = config['population']['initialization_strategy']
    n_random = int(pop_size * strat['random_valid'])
    n_time   = int(pop_size * strat['greedy_time'])
    n_friend = pop_size - n_random - n_time

    student_ids = list(students.keys())
    population  = []

    # helper to build one individual using a given strategy
    def make_individual(strategy, friend_schedules=None):
        chromosome = {}
        for sid in student_ids:
            if strategy == 'random':
                entries = init_random_valid(sid, students, courses)
            elif strategy == 'time':
                entries = init_greedy_time(sid, students, courses)
            else:
                entries = init_greedy_friend(sid, students, courses, friend_schedules)
            chromosome[sid] = entries
        return {'chromosome': chromosome, 'fitness': None}

    # add random valid individuals
    for _ in range(n_random):
        population.append(make_individual('random'))

    # add greedy time-based individuals
    for _ in range(n_time):
        population.append(make_individual('time'))

    # add friend-based individuals, building context incrementally
    for _ in range(n_friend):
        friend_sched = {}
        for sid in student_ids:
            entries = init_greedy_friend(sid, students, courses, friend_sched)
            friend_sched[sid] = entries
        population.append({'chromosome': friend_sched, 'fitness': None})

    return population


def copy_chromosome(chromosome):
    return deep_copy_chromosome(chromosome)


# prints a human-readable summary of one chromosome
def describe_chromosome(chromosome, students, courses):
    for sid in sorted(chromosome.keys()):
        s = students[sid]
        print(f"\n  {sid} ({s['name']}):")
        for entry in chromosome[sid]:
            cname = courses[entry['course_id']]['name']
            slots = ', '.join(f"{d} {t}:00" for d, t in entry['days_times'])
            print(f"    {entry['course_id']} Sec{entry['section_id']} - {cname} [{slots}]")