from utils import (
    get_section_schedule, has_time_conflict, violates_blocked_time,
    prerequisites_satisfied, max_courses_per_day, total_credits,
    DAYS_ORDER
)


# counts how many class meetings fall in the student's preferred time slots
def calc_time_preference(student_id, student_courses, students, courses):
    s = students[student_id]
    preferred = set(s['time_preferences']['preferred']['time_slots'])

    total_meetings = 0
    preferred_hits = 0

    for entry in student_courses:
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        for slot in sched:
            total_meetings += 1
            if slot['time'] in preferred:
                preferred_hits += 1

    # return neutral score if student has no classes
    if total_meetings == 0:
        return 0.5
    return preferred_hits / total_meetings


# measures how many idle hours exist between first and last class each day
def calc_gap_score(student_id, student_courses, students, courses):
    # group all class times by day
    day_times = {}
    for entry in student_courses:
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        for slot in sched:
            day = slot['day']
            if day not in day_times:
                day_times[day] = []
            day_times[day].append(slot['time'])

    if not day_times:
        return 1.0

    total_gap = 0
    max_possible = 0

    for day, times in day_times.items():
        if len(times) < 2:
            continue
        first = min(times)
        last  = max(times)
        span  = last - first + 1
        gap   = span - len(times)
        total_gap    += gap
        max_possible += span - 1

    if max_possible == 0:
        return 1.0
    return 1.0 - (total_gap / max_possible)


# helper to get friend ids for a given student from friend_pairs list
def get_friends(student_id, friend_pairs):
    friends = []
    for pair in friend_pairs:
        if student_id in pair:
            # add the other person in the pair
            if pair[0] == student_id:
                friends.append(pair[1])
            else:
                friends.append(pair[0])
    return friends


# scores how many (course, section) pairs this student shares with friends
def calc_friend_score(student_id, student_courses, all_chromosomes, friend_pairs, courses):
    friends = get_friends(student_id, friend_pairs)

    if not friends:
        return 1.0

    # build set of (course_id, section_id) for this student
    my_sections = set()
    for e in student_courses:
        my_sections.add((e['course_id'], e['section_id']))

    total_possible = 0
    total_shared   = 0

    for fid in friends:
        if fid not in all_chromosomes:
            continue

        # build set of (course_id, section_id) for the friend
        friend_sections = set()
        for e in all_chromosomes[fid]:
            friend_sections.add((e['course_id'], e['section_id']))

        shared   = my_sections & friend_sections
        possible = len(my_sections | friend_sections)
        total_shared   += len(shared)
        total_possible += possible

    if total_possible == 0:
        return 1.0
    return min(1.0, total_shared / total_possible)


# penalises days where 3 or more hard-difficulty courses are scheduled
def calc_workload_balance(student_id, student_courses, students, courses):
    # track difficulty levels per day
    day_difficulties = {}
    for entry in student_courses:
        diff  = courses[entry['course_id']]['difficulty']
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        for slot in sched:
            day = slot['day']
            if day not in day_difficulties:
                day_difficulties[day] = []
            day_difficulties[day].append(diff)

    if not day_difficulties:
        return 1.0

    violations = 0
    for day, diffs in day_difficulties.items():
        hard_count = 0
        for d in diffs:
            if d == 3:
                hard_count += 1
        if hard_count >= 3:
            violations += 1

    return 1.0 - (violations / len(day_difficulties))


# rewards having the 12PM slot free on multiple days
def calc_lunch_break(student_id, student_courses, students, courses, lunch_time=12,
                     min_free_days=3):
    # find which days have a class at lunch time
    days_with_lunch_class = set()
    for entry in student_courses:
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        for slot in sched:
            if slot['time'] == lunch_time:
                days_with_lunch_class.add(slot['day'])

    # find all days the student has any class
    days_with_class = set()
    for entry in student_courses:
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        for slot in sched:
            days_with_class.add(slot['day'])

    active_days = len(days_with_class) if days_with_class else 5
    free_lunch_days = active_days - len(days_with_lunch_class)

    return min(1.0, free_lunch_days / min_free_days)


# adds up all hard constraint penalties for one student
def calc_penalties(student_id, student_courses, students, courses, penalty_cfg):
    s         = students[student_id]
    completed = set(s['completed_courses'])
    blocked   = s['time_preferences']['blocked']['slots']
    total_penalty = 0

    P_HARD = penalty_cfg.get('hard_constraint', -1000)
    P_TC   = penalty_cfg.get('time_conflict',   -1000)
    P_CR   = penalty_cfg.get('missing_credits', -800)
    P_DAY  = penalty_cfg.get('too_many_courses', -500)
    P_BLK  = penalty_cfg.get('blocked_time',    -1000)

    # check credit count matches required
    course_ids = [e['course_id'] for e in student_courses]
    credits = total_credits(course_ids, courses)
    if credits != s['required_credits']:
        total_penalty += P_CR

    # check every pair of courses for time conflicts
    for i in range(len(student_courses)):
        for j in range(i + 1, len(student_courses)):
            si = get_section_schedule(courses, student_courses[i]['course_id'], student_courses[i]['section_id'])
            sj = get_section_schedule(courses, student_courses[j]['course_id'], student_courses[j]['section_id'])
            if has_time_conflict(si, sj):
                total_penalty += P_TC

    # check prerequisites are satisfied
    for entry in student_courses:
        if not prerequisites_satisfied(entry['course_id'], courses, completed):
            total_penalty += P_HARD

    # check no day has too many courses
    day_counts = {}
    for entry in student_courses:
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        for slot in sched:
            if slot['day'] not in day_counts:
                day_counts[slot['day']] = 0
            day_counts[slot['day']] += 1
    for count in day_counts.values():
        if count > s['max_courses_per_day']:
            total_penalty += P_DAY

    # check no class falls in a blocked time slot
    for entry in student_courses:
        sched = get_section_schedule(courses, entry['course_id'], entry['section_id'])
        if violates_blocked_time(sched, blocked):
            total_penalty += P_BLK

    return total_penalty


# calculates weighted fitness + penalty for one student, returns score and breakdown
def student_fitness(student_id, student_courses, students, courses,
                    all_chromosomes, friend_pairs, weights, penalty_cfg):
    s_time     = calc_time_preference(student_id, student_courses, students, courses)
    s_gap      = calc_gap_score(student_id, student_courses, students, courses)
    s_friend   = calc_friend_score(student_id, student_courses, all_chromosomes, friend_pairs, courses)
    s_workload = calc_workload_balance(student_id, student_courses, students, courses)
    s_lunch    = calc_lunch_break(student_id, student_courses, students, courses)
    penalty    = calc_penalties(student_id, student_courses, students, courses, penalty_cfg)

    w = weights
    weighted = (w['time_preference']     * s_time +
                w['gap_minimization']    * s_gap  +
                w['friend_satisfaction'] * s_friend +
                w['workload_balance']    * s_workload +
                w['lunch_break']         * s_lunch)

    # penalty is already negative so this subtracts from fitness
    total = weighted + penalty

    breakdown = {
        'time':     s_time,
        'gap':      s_gap,
        'friend':   s_friend,
        'workload': s_workload,
        'lunch':    s_lunch,
        'penalty':  penalty,
        'weighted': weighted,
        'total':    total,
    }
    return total, breakdown


# evaluates one individual and stores fitness + breakdown inside it
def evaluate_fitness(individual, students, courses, friend_pairs, config):
    chromosome  = individual['chromosome']
    weights     = config['fitness']['weights']
    penalty_cfg = config['fitness']['penalties']

    total_fit  = 0.0
    breakdowns = {}

    for sid, student_courses in chromosome.items():
        fit, bd = student_fitness(
            sid, student_courses, students, courses,
            chromosome, friend_pairs, weights, penalty_cfg
        )
        total_fit += fit
        breakdowns[sid] = bd

    # average fitness across all students
    avg_fit = total_fit / len(chromosome) if chromosome else 0.0
    individual['fitness']   = avg_fit
    individual['breakdown'] = breakdowns
    return avg_fit


# runs evaluate_fitness on every individual in the population
def evaluate_population(population, students, courses, friend_pairs, config):
    for ind in population:
        evaluate_fitness(ind, students, courses, friend_pairs, config)