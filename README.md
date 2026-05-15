# Q2 – Genetic Algorithm: University Course Scheduling Optimizer

This folder contains my Genetic Algorithm (GA) solution for the university course scheduling problem. The GA builds weekly schedules for a small set of students by picking course sections in a way that avoids clashes and blocked timings, and then tries to improve the schedules based on preferences.

The scheduling part has two sides:
- Hard constraints (must be satisfied): correct credits, no time conflicts, prerequisites satisfied, and blocked times avoided.
- Soft goals (try to improve): preferred time slots, fewer gaps between classes, friend overlap, balanced workload, and lunch break availability.

## Folder / File Layout

```
Q2_GA/
├── main.py # runs the GA loop (single run / multi-run depending on args)
├── chromosome.py # chromosome representation + initial population creation
├── fitness.py # fitness scoring (soft goals) + penalties (hard constraints)
├── operators.py # crossover + mutation operators + repair functions
├── selection.py # parent selection + elitism + diversity injection
├── utils.py # loading data + checking conflicts/constraints + helpers
├── make_data.py # optional: helper script (if you want to regenerate data files)
├── config.yaml # all GA settings (population size, rates, weights, stopping rules)
├── README.md
├── data/ # input data files needed to run the project (CSV files + JSON files)
├── results/ # saved runs / logs / best schedules (generated after running)
└── plots/ # graphs saved after running (generated after running)
```

Note: I did not include IDE folders like .idea, environments like .venv, or cache folders like __pycache__ in the repo.

---

## How a schedule is stored (chromosome idea)

Each solution (chromosome) stores a schedule for each student. The important part is that a student is assigned to a course AND a section.

A schedule entry has:
- course_id
- section_id
- days_times (this is derived from the course/section info)

Important design choice: section_id is the binding field. That means the actual day/time of a class comes from the chosen section in the data. Mutations do not directly edit day/time. They just change the section, and the meeting times update automatically when the entry is rebuilt.

---

## How to run

1) Go into the folder:

```bash
cd Q2_GA
```

2) Install dependencies:

```bash
pip install -r requirements.txt
```

If you don’t have requirements.txt, this usually works:

```bash
pip install pyyaml matplotlib
```

3) Make sure the data/ folder exists and contains the CSV files the program expects (these are the inputs for courses/sections and student requirements).

4) Run the GA:

```bash
python main.py
```

If main.py supports extra arguments (like seed, runs, etc.), you can use them the same way, for example:

```bash
python main.py --single --seed 42
```

After it runs, you should see outputs in:
- results/ (saved schedules / logs)
- plots/ (fitness/diversity plots, depending on what the code is set to generate)

---

## What the main parts do

- main.py: runs the GA loop and handles saving results.
- chromosome.py: stores the schedule structure and builds the starting population.
- fitness.py: calculates fitness (soft goals) and subtracts penalties (hard constraint breaks).
- selection.py: chooses parents and applies elitism / diversity injection.
- operators.py: does crossover + mutation, and repairs schedules by trying different sections.
- utils.py: loads data and contains helpers like conflict checks.

---

## Notes about the data

The input data is stored inside the data/ folder as CSV files. These files contain:
- course + section info (including day/time for each section and prerequisites)
- student requirements (required courses, completed courses, time preferences, friend pairs, etc.)

If make_data.py is used in your setup, it’s optional and only needed if you want to regenerate the data files.

---

## Academic Integrity

All GA logic (chromosome representation, fitness scoring, selection, crossover, mutation, repair, and the main GA loop) was implemented by me.

For the visuals/GUI part, I took help from Claude to build the interface and improve the look, but the scheduling algorithm and GA implementation are my own work.