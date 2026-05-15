import random
import copy
import os
import sys
import time
import argparse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils import (
    load_courses, load_students, load_config,
    population_diversity, chromosome_signature,
    DAYS_ORDER, format_time
)
from chromosome import initialise_population, describe_chromosome
from fitness import evaluate_fitness, evaluate_population
from selection import select_parents, apply_elitism, inject_random_individuals
from operators import crossover, mutate, get_adaptive_rates


# checks if any of the 3 stopping conditions are met
def should_terminate(generation, best_history, population, config):
    term = config['termination']

    # condition 1: max generations reached
    if generation >= term['max_generations']:
        return True, f"Max generations ({term['max_generations']}) reached"

    # condition 2: fitness hasn't improved enough over last N generations
    if term['convergence']['enabled']:
        patience  = term['convergence']['patience']
        threshold = term['convergence']['improvement_threshold']
        if len(best_history) >= patience:
            recent           = best_history[-patience:]
            best_in_window   = max(recent)
            oldest_in_window = recent[0]
            if oldest_in_window != 0:
                improvement = abs(best_in_window - oldest_in_window) / abs(oldest_in_window)
            else:
                improvement = abs(best_in_window - oldest_in_window)
            if improvement < threshold:
                return True, f"Stagnation: <{threshold*100:.1f}% improvement in {patience} gens"

    # condition 3: most of the population has similar fitness
    if term['similarity']['enabled']:
        sim_threshold = term['similarity']['threshold']
        tolerance     = term['similarity']['tolerance']
        fitnesses     = [ind['fitness'] for ind in population if ind['fitness'] is not None]
        if fitnesses:
            avg_fit = sum(fitnesses) / len(fitnesses)
            if avg_fit != 0:
                # count how many individuals are within tolerance of the average
                similar = 0
                for f in fitnesses:
                    if abs(f - avg_fit) / max(abs(avg_fit), 1e-9) <= tolerance:
                        similar += 1
                if similar / len(fitnesses) >= sim_threshold:
                    pct = similar / len(fitnesses) * 100
                    tol_pct = tolerance * 100
                    return True, f"Population convergence: {pct:.0f}% within ±{tol_pct:.0f}%"

    return False, ""


# runs one full GA run and returns all history + best individual
def run_ga(students, courses, friend_pairs, global_constraints, config,
           seed=None, verbose=True, run_id=1):
    if seed is not None:
        random.seed(seed)

    pop_size         = config['population']['size']
    base_rates       = config['mutation']['base_rates']
    div_cfg          = config['diversity']['maintenance']
    check_interval   = config['mutation']['adaptive']['check_interval']
    adaptive_enabled = config['mutation']['adaptive']['enabled']

    if verbose:
        print(f"\n{'='*55}")
        print(f"  GA Run {run_id}  (seed={seed})")
        print(f"{'='*55}")

    # create starting population
    population = initialise_population(pop_size, students, courses, config)
    evaluate_population(population, students, courses, friend_pairs, config)

    best_history  = []
    avg_history   = []
    worst_history = []
    div_history   = []
    conv_gen      = None
    current_rates = dict(base_rates)

    start_time = time.time()

    for gen in range(config['termination']['max_generations']):

        # check diversity every N generations and inject if too low
        if gen % check_interval == 0:
            diversity = population_diversity(population)
            div_history.append(diversity)

            if adaptive_enabled:
                current_rates = get_adaptive_rates(base_rates, diversity, config)

            if div_cfg['enabled'] and diversity < div_cfg['low_threshold']:
                n_inject = int(pop_size * div_cfg['injection_rate'])
                population = inject_random_individuals(population, n_inject, students, courses, config)
                evaluate_population(population, students, courses, friend_pairs, config)
        else:
            diversity = div_history[-1] if div_history else 1.0

        # breed the next generation
        new_population = []
        while len(new_population) < pop_size:
            p1, p2 = select_parents(population, config)

            c1_chrom, c2_chrom = crossover(p1, p2, students, courses, config)
            c1 = {'chromosome': c1_chrom, 'fitness': None}
            c2 = {'chromosome': c2_chrom, 'fitness': None}

            c1 = mutate(c1, students, courses, config, friend_pairs, current_rates)
            c2 = mutate(c2, students, courses, config, friend_pairs, current_rates)

            new_population.extend([c1, c2])

        new_population = new_population[:pop_size]
        evaluate_population(new_population, students, courses, friend_pairs, config)

        # keep the best individuals from the old generation
        new_population = apply_elitism(population, new_population, config)
        population = new_population

        # record stats for this generation
        fitnesses = [ind['fitness'] for ind in population]
        best_fit  = max(fitnesses)
        avg_fit   = sum(fitnesses) / len(fitnesses)
        worst_fit = min(fitnesses)

        best_history.append(best_fit)
        avg_history.append(avg_fit)
        worst_history.append(worst_fit)

        if verbose and gen % config['logging']['console']['frequency'] == 0:
            scaled = current_rates != base_rates
            print(f"  Gen {gen:>4} | best={best_fit:.4f}  avg={avg_fit:.4f}  "
                  f"worst={worst_fit:.4f}  div={diversity:.2f}  rates_scaled={scaled}")

        # check if we should stop early
        stop, reason = should_terminate(gen + 1, best_history, population, config)
        if stop:
            conv_gen = gen + 1
            if verbose:
                print(f"\n  [STOP at gen {conv_gen}] {reason}")
            break

    elapsed  = time.time() - start_time
    best_ind = max(population, key=lambda i: i['fitness'])

    if verbose:
        print(f"\n  Best fitness : {best_ind['fitness']:.4f}")
        print(f"  Elapsed      : {elapsed:.2f}s")
        print(f"  Converged at : gen {conv_gen or len(best_history)}")

    return {
        'best':          best_ind,
        'best_history':  best_history,
        'avg_history':   avg_history,
        'worst_history': worst_history,
        'div_history':   div_history,
        'conv_gen':      conv_gen or len(best_history),
        'elapsed':       elapsed,
        'run_id':        run_id,
        'seed':          seed,
    }


# runs the GA multiple times with different seeds and collects results
def run_experiments(students, courses, friend_pairs, global_constraints, config, num_runs=10):
    print("\n" + "=" * 55)
    print(f"  RUNNING {num_runs} INDEPENDENT GA RUNS")
    print("=" * 55)

    seeds   = [42 + i * 13 for i in range(num_runs)]
    results = []

    for i, seed in enumerate(seeds):
        res = run_ga(students, courses, friend_pairs, global_constraints,
                     config, seed=seed, verbose=True, run_id=i + 1)
        results.append(res)

    # print summary statistics across all runs
    best_fits = [r['best']['fitness'] for r in results]
    conv_gens = [r['conv_gen'] for r in results]
    elapseds  = [r['elapsed'] for r in results]

    import statistics as st
    print("\n" + "=" * 55)
    print("MULTI-RUN SUMMARY")
    print("=" * 55)
    print(f"  Best fitness  : {max(best_fits):.4f}")
    print(f"  Avg fitness   : {sum(best_fits)/len(best_fits):.4f}")
    print(f"  Std dev       : {st.stdev(best_fits):.4f}")
    print(f"  Avg conv gen  : {sum(conv_gens)/len(conv_gens):.1f}")
    print(f"  Avg runtime   : {sum(elapseds)/len(elapseds):.2f}s")

    # save plots
    _plot_convergence(results)
    _plot_diversity(results)
    _plot_operator_comparison(results)

    # print the best schedule found across all runs
    best_run = max(results, key=lambda r: r['best']['fitness'])
    print(f"\n  Best run: Run {best_run['run_id']} (seed={best_run['seed']})")
    print_best_schedule(best_run['best'], students, courses, friend_pairs)

    return results


# saves convergence plot showing best/avg/worst fitness per run
def _plot_convergence(results):
    os.makedirs('plots', exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6))

    colors = plt.cm.tab10.colors
    for i, r in enumerate(results):
        gens  = range(len(r['best_history']))
        color = colors[i % len(colors)]
        ax.plot(gens, r['best_history'],  color=color, linewidth=1.2, label=f"Run {r['run_id']} best", alpha=0.8)
        ax.plot(gens, r['avg_history'],   color=color, linewidth=0.7, linestyle='--', alpha=0.4)
        ax.plot(gens, r['worst_history'], color=color, linewidth=0.5, linestyle=':', alpha=0.3)

    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Fitness', fontsize=12)
    ax.set_title('Convergence Analysis – Best/Avg/Worst Fitness (10 Runs)', fontsize=13)
    ax.legend(fontsize=7, ncol=2, loc='lower right')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = 'plots/convergence.png'
    plt.savefig(path, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"\n  [Plot] {path}")


# saves diversity plot showing how unique the population stays over time
def _plot_diversity(results):
    os.makedirs('plots', exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))

    colors = plt.cm.tab10.colors
    for i, r in enumerate(results):
        if r['div_history']:
            gens = [g * 10 for g in range(len(r['div_history']))]
            ax.plot(gens, r['div_history'], color=colors[i % len(colors)],
                    linewidth=1.2, label=f"Run {r['run_id']}", alpha=0.8,
                    marker='o', markersize=3)

    ax.axhline(0.30, color='red', linestyle='--', linewidth=1.5, label='Diversity threshold (30%)')
    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Diversity (fraction unique)', fontsize=12)
    ax.set_title('Population Diversity Over Generations', fontsize=13)
    ax.legend(fontsize=7, ncol=2)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    path = 'plots/diversity.png'
    plt.savefig(path, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"  [Plot] {path}")


# saves bar charts comparing best fitness and convergence gen across runs
def _plot_operator_comparison(results):
    os.makedirs('plots', exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Operator Analysis – Run Comparison', fontsize=13, fontweight='bold')

    run_ids   = [r['run_id'] for r in results]
    best_fits = [r['best']['fitness'] for r in results]
    conv_gens = [r['conv_gen'] for r in results]

    # highlight the best run in a different color
    max_fit = max(best_fits)
    colors  = []
    for f in best_fits:
        if f == max_fit:
            colors.append('#4ECDC4')
        else:
            colors.append('#e94560')

    ax1.bar(run_ids, best_fits, color=colors, alpha=0.85)
    ax1.set_xlabel('Run')
    ax1.set_ylabel('Best Fitness')
    ax1.set_title('Best Fitness per Run')
    ax1.grid(axis='y', alpha=0.3)

    ax2.bar(run_ids, conv_gens, color='#45B7D1', alpha=0.85)
    ax2.set_xlabel('Run')
    ax2.set_ylabel('Convergence Generation')
    ax2.set_title('Convergence Generation per Run')
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = 'plots/operator_analysis.png'
    plt.savefig(path, dpi=130, bbox_inches='tight')
    plt.close()
    print(f"  [Plot] {path}")


# prints the full schedule for the best individual found
def print_best_schedule(best_ind, students, courses, friend_pairs):
    chromosome = best_ind['chromosome']
    breakdown  = best_ind.get('breakdown', {})

    print("\n" + "=" * 65)
    print("         BEST SCHEDULE – WEEKLY TIMETABLE")
    print("=" * 65)

    for sid in sorted(chromosome.keys()):
        s_data  = students[sid]
        entries = chromosome[sid]
        bd      = breakdown.get(sid, {})

        print(f"\n{'─'*65}")
        print(f"  {sid}: {s_data['name']}  (Year {s_data['year']})")
        print(f"  Fitness breakdown: time={bd.get('time',0):.2f}  "
              f"gap={bd.get('gap',0):.2f}  friend={bd.get('friend',0):.2f}  "
              f"workload={bd.get('workload',0):.2f}  lunch={bd.get('lunch',0):.2f}  "
              f"penalty={bd.get('penalty',0)}")
        print(f"  {'Course':<10} {'Name':<30} {'Sec':>4}  Schedule")
        print(f"  {'─'*60}")

        for entry in entries:
            cname = courses[entry['course_id']]['name']
            # build slot string manually
            slot_parts = []
            for d, t in entry['days_times']:
                slot_parts.append(f"{d[:3]} {format_time(t)}")
            slots = ', '.join(slot_parts)
            print(f"  {entry['course_id']:<10} {cname:<30} Sec{entry['section_id']}  {slots}")

    _print_weekly_grid(chromosome, students, courses)
    _print_friend_overlaps(chromosome, students, courses, friend_pairs)

    print("\n" + "=" * 65)
    print(f"  Overall fitness: {best_ind['fitness']:.4f}")
    print("=" * 65)


# prints a text grid of the weekly timetable
def _print_weekly_grid(chromosome, students, courses):
    print("\n" + "=" * 65)
    print("WEEKLY GRID VIEW")
    print("=" * 65)

    days        = DAYS_ORDER
    times       = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    student_ids = sorted(chromosome.keys())
    time_w      = 6
    day_w       = 11

    # build lookup: (student, day, time) -> course_id
    lookup = {}
    for sid, entries in chromosome.items():
        for entry in entries:
            for (d, t) in entry['days_times']:
                lookup[(sid, d, t)] = entry['course_id']

    # print day headers
    header = f"{'Time':<{time_w}}"
    for day in days:
        header += f"  {day[:3]:<{day_w}}"
    print(header)
    print('─' * len(header))

    # print one row per time slot
    for t in times:
        row = f"{format_time(t):<{time_w}}"
        for day in days:
            entries_here = []
            for sid in student_ids:
                cid = lookup.get((sid, day, t))
                if cid:
                    entries_here.append(f"{cid}({sid[-1]})")
            cell = ','.join(entries_here) if entries_here else '.'
            row += f"  {cell:<{day_w}}"
        print(row)


# prints which classes each friend pair shares
def _print_friend_overlaps(chromosome, students, courses, friend_pairs):
    print("\n" + "=" * 65)
    print("FRIEND OVERLAP SUMMARY")
    print("=" * 65)

    for pair in friend_pairs:
        sa, sb = pair[0], pair[1]

        # build (course, section) sets for each student
        secs_a = set()
        for e in chromosome.get(sa, []):
            secs_a.add((e['course_id'], e['section_id']))
        secs_b = set()
        for e in chromosome.get(sb, []):
            secs_b.add((e['course_id'], e['section_id']))

        shared = secs_a & secs_b
        print(f"  {sa} ↔ {sb}: {len(shared)} shared class(es)")
        for (cid, sec) in sorted(shared):
            cname = courses[cid]['name']
            print(f"    • {cid} Sec{sec} – {cname}")
        if not shared:
            print(f"    (no shared classes)")


def parse_args():
    p = argparse.ArgumentParser(description='Q2: GA Course Scheduling')
    p.add_argument('--runs',     type=int,            default=10,  help='Number of GA runs')
    p.add_argument('--seed',     type=int,            default=42,  help='Seed for single run')
    p.add_argument('--single',   action='store_true',              help='Single run mode')
    p.add_argument('--gui',      action='store_true',              help='Launch GUI after run')
    p.add_argument('--courses',  default='course_catalog.json')
    p.add_argument('--students', default='student_requirements.json')
    p.add_argument('--config',   default='config.yaml')
    return p.parse_args()


def main():
    args = parse_args()

    # load all data files
    courses  = load_courses(args.courses)
    students, friend_pairs, global_constraints = load_students(args.students)
    config   = load_config(args.config)

    print("\n" + "=" * 55)
    print("  Q2: Genetic Algorithm – Course Scheduling")
    print("=" * 55)
    print(f"  Students : {len(students)}")
    print(f"  Courses  : {len(courses)}")
    print(f"  Pop size : {config['population']['size']}")
    print(f"  Max gens : {config['termination']['max_generations']}")

    if args.single:
        result = run_ga(students, courses, friend_pairs, global_constraints,
                        config, seed=args.seed, verbose=True, run_id=1)
        print_best_schedule(result['best'], students, courses, friend_pairs)
        results = [result]
    else:
        results = run_experiments(students, courses, friend_pairs,
                                  global_constraints, config, num_runs=args.runs)

    if args.gui:
        from gui import launch_gui
        best = max(results, key=lambda r: r['best']['fitness'])
        launch_gui(best, results, students, courses, friend_pairs)

    return results


if __name__ == '__main__':
    main()