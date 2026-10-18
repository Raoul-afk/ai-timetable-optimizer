# AI timetable optimizer

## Shared problem definition

The datasets describe five semesters (S1, S3, S5, S7, S9), with four independent groups per semester. Each course has one teacher, and its `sessions` value is the number of weekly lessons **per group**. Each lesson occupies one two-hour timeslot.

A valid timetable must satisfy these hard constraints:

1. A room can host at most one lesson per timeslot.
2. A group can attend at most one lesson per timeslot.
3. A teacher can teach at most one lesson per timeslot.

Different groups in the same semester may have lessons at the same time. There are no room capacity, equipment, or availability restrictions.

The Hill Climbing fitness is the total number of conflicting pairs across the three constraints. `same_course_conflicts` is reported for diagnosis but is not added separately: lessons of the same course already share a teacher.

## Data

The JSON files are in [`data/`](data/):

- `data_12_rooms.json`
- `data_15_rooms.json`
- `data_20_rooms.json`

The solver uses `data_20_rooms.json` by default. To switch datasets, update `DATA_FILE` in [`algo/hill-climbing.py`](algo/hill-climbing.py).

## Hill Climbing

The search combines greedy hill climbing, random walk, and random restarts:

- With probability `p_greedy`, it evaluates a sample of neighboring schedules and takes the best non-worsening one.
- Otherwise, it takes a random neighbor, even if its fitness is worse.
- It restarts from a new random schedule up to `max_restarts` times and keeps the best result.

The search parameters (`max_restarts`, `max_steps`, `p_greedy`, `sample_size`, and `seed`) are set in the call to `hill_climbing_search()` in [`algo/hill-climbing.py`](algo/hill-climbing.py). A fitness of `0` means all hard constraints are satisfied; the search does not guarantee that it will find one.

Run from the repository root with Python 3:

```bash
python algo/hill-climbing.py
```

The project uses only the Python standard library. The script prints the search metrics and generated timetable to the console.

## DFS and backtracking

The backtracking solver uses the same dataset and constraints described above. It can be run in three configurations to compare variable/value ordering:

```bash
# Plain DFS, fixed input order
python algo/dfs_backtracking_timetable.py --no-mrv --no-degree --output dfs_plain.csv

# DFS with MRV
python algo/dfs_backtracking_timetable.py --no-degree --output dfs_mrv.csv

# DFS with MRV and the degree tie-breaker (default)
python algo/dfs_backtracking_timetable.py --output dfs_mrv_degree.csv
```

The solver applies:

1. **MRV** to choose the unassigned session with the fewest available timeslots.
2. **Degree** as a tie-breaker, preferring the session sharing a group or teacher with the most unassigned sessions.
3. **Backtracking** to undo an assignment when it leads to a dead end.
4. **Forward checking** to stop a branch if any unassigned session has no available timeslot.

Because rooms are interchangeable in the current datasets, the solver only needs to try one free room for each timeslot. This optimization must be revisited if room capacities, equipment, or preferences are added.

`FEASIBLE` means all sessions were assigned; `NO_SOLUTION` means the search was exhausted; `SEARCH_LIMIT` means the time or node budget was reached and does not prove that no solution exists. The DFS search statistics (`nodes_explored`, `backtracks`, and `domain_checks`) count different operations from Hill Climbing's `total_evaluations`, so compare runtime and validity rather than comparing those counts directly.

## Genetic Algorithm

The search uses a pure genetic algorithm with uniform crossover, targeted mutation, and elitism:

- With a tournament of size `k`, it selects the best individual among random candidates to become parents.
- With a uniform crossover, each gene of the child is randomly inherited from one of the two parents.
- With a small mutation probability, a gene is modified by changing either its room or its timeslot.
- The top 5 individuals are preserved unchanged at each generation to keep the best solutions.

The search parameters (`pop_size`, `generations`, `gene_mutation_prob`, `k`) are set in the call to `run_pure_ga()` in [`algo/genetic.py`](algo/genetic.py). A fitness of `0` (i.e., 0 conflicts) means all hard constraints are satisfied; the search does not guarantee that it will find one within the given generations.

Run from the repository root with Python 3:

```bash
python algo/genetic.py
