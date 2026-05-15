# University Course Scheduling Optimizer using Genetic Algorithm

A Genetic Algorithm (GA)-based solution for the university course scheduling problem. This optimizer builds weekly schedules for a group of students by assigning course sections, aiming to maximize scheduling preferences and satisfy constraints.

## Features

- Handles hard constraints: required credits, no time conflicts, prerequisite satisfaction, and blocking unavailable times.
- Optimizes soft goals: preferred time slots, fewer gaps between classes, overlap with friends, balanced workload, and lunch break availability.
- Modular, extensible codebase for customization.

## Project Structure

```
GA/
├── main.py           # Runs the GA loop (single/multi-run based on arguments)
├── chromosome.py     # Chromosome representation and initial population creation
├── fitness.py        # Fitness scoring (soft goals) and penalties (hard constraints)
├── operators.py      # Crossover, mutation operators, and repair functions
├── selection.py      # Parent selection, elitism, and diversity injection
├── utils.py          # Data loading, conflict/constraint checking, helpers
├── make_data.py      # (Optional) Helper script to regenerate data files
├── config.yaml       # GA settings (population size, rates, weights, stopping rules)
├── README.md
├── data/             # Input data files needed to run the project (CSV and JSON)
└── plots/            # Graphs saved after running (e.g., fitness/diversity plots)
```

> **Note:** IDE folders like `.idea`, environments such as `.venv`, and cache folders like `__pycache__` are not included in the repo.

---

## Chromosome & Schedule Representation

Each solution (chromosome) stores a schedule for each student, assigning both a course and a section.

A schedule entry includes:

- `course_id`
- `section_id`
- `days_times` (derived from section info)

**Design note:** The section ID binds the schedule entry to a specific class time. Mutations operate by selecting different sections (not editing class times directly).

---

## Getting Started

1. **Navigate to the project folder:**
    ```bash
    cd GA
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    If `requirements.txt` is missing, install core dependencies directly:
    ```bash
    pip install pyyaml matplotlib
    ```

3. **Prepare data:**
    - Ensure the `data/` folder exists and contains required CSV files (for courses/sections, student requirements, etc.).

4. **Run the optimizer:**
    ```bash
    python main.py
    ```
    For custom runs or seeds:
    ```bash
    python main.py --single --seed 42
    ```

5. **Outputs:**
    - Scheduling and analysis results (e.g., fitness/diversity plots) are saved inside the `plots/` folder.

---

## Data Format

Input data lives in the `data/` folder as CSV files, including:

- Courses and sections (with day/time, prerequisites, etc.)
- Student requirements (courses needed, completed courses, time preferences, friend pairs, etc.)

The `make_data.py` script is optional; use it if you wish to regenerate the data files.

---

## File Descriptions

- **main.py**: Runs the genetic algorithm loop and manages outputs.
- **chromosome.py**: Chromosome structure and initial population setup.
- **fitness.py**: Calculates fitness (soft goals) and applies penalties (hard constraints).
- **selection.py**: Parent selection process, elitism, and diversity measures.
- **operators.py**: Crossover, mutation, and repair mechanisms.
- **utils.py**: Data loading, conflict and constraint checking, helper functions.

---

## Credits

- Scheduling algorithm and core GA implementation by @shahramshafiq.
