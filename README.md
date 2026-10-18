# ai-timetable-optimizer

# Department timetable — Hill Climbing with Random Walk and Random Restart

## Model

- S1, S3, S5, S7, S9: the first semesters of five university years.
- Four independent groups per semester: `S1_G1` through `S9_G4`.
- Each course has one assigned teacher across **all four groups**.
- `sessions` in the JSON means the number of weekly sessions of this course **for each group**.
- All sessions occupy one 2-hour time block; `MON_08` = 08:00–10:00, etc.

## Hard constraints

1. Same `(room, timeslot)` is forbidden for multiple sessions.
2. Same `(group, timeslot)` is forbidden for multiple sessions.
3. Same `(teacher, timeslot)` is forbidden for multiple sessions, even across semesters.

**Different groups of the same semester may have different courses simultaneously.** With one teacher per course, two groups taking the *same* course simultaneously violate constraint #3. No conflict is counted solely because two sessions belong to the same semester.

The numeric heuristic counts each conflicting pair once **per constraint category**. `same_course_conflicts` is reported for diagnostic purposes but is *not* added separately to the fitness: under the single-teacher-per-course assumption, it is already included in `teacher_conflicts`.

## Run

Requires only Python 3 (standard library).

```bash
python generate_data_hard.py   # optional; data_hard.json is already included
python hill_climbing_timetable.py
```

In `hill_climbing_timetable.py`, configure the search with `max_restarts`, `max_steps`, `p_greedy`, `sample_size` and `seed`. The shipped defaults (`5` restarts × `300` iterations, `35` sampled greedy neighbors, `0.85` greedy probability) provide a manageable test run, not a guarantee of zero conflicts. A conflict-free schedule is possible with the 50-room data, but the method does not guarantee success for every seed or dataset.

The `schedule_example.csv` is a sample result for **50 rooms**, using the default configuration with seed `42`. See `schedule_metrics.json` for the associated scores. Its fitness is **0**, with no room, group or teacher conflicts.

## Data size

- 25 unique courses = 5 courses × 5 semesters.
- 20 groups = 4 groups × 5 semesters.
- 200 sessions = 25 courses × 4 groups × 2 sessions.
- **50 rooms** (R101–R150), 20 weekly two-hour timeslots.
- Optional benchmark datasets: `data_12_rooms.json` and `data_20_rooms.json`. The solver uses `data_hard.json` (50 rooms) by default.

## Program components

- `generate_data_hard.py`: deterministic sample dataset generator.
- `data_hard.json`: generated 50-room dataset.
- `data_12_rooms.json` / `data_20_rooms.json`: alternative room-count datasets for comparisons.
- `hill_climbing_timetable.py`: solver, fitness and CLI report.
- `schedule_example.csv`: exported sample timetable.
- `schedule_metrics.json`: metrics for that example.

## Room-count experiment (single run, seed 42)

| Rooms | Fitness (lower is better) | Room / group / teacher conflicts | Fitness evaluations | Runtime (s) |
| ---: | ---: | --- | ---: | ---: |
| 12 | 4 | 4 / 0 / 0 | 45,433 | 8.58 |
| 20 | 0 | 0 / 0 / 0 | 23,225 | 4.23 |
| 50 | 0 | 0 / 0 / 0 | 3,550 | 0.66 |

These are illustrative individual runs, **not average performance benchmarks**. Repeat across multiple seeds before drawing comparative conclusions. Runtime depends on hardware. With no room-specific restrictions, at most 20 sessions (one per group) can occur concurrently, so 20 rooms are theoretically sufficient from a room-capacity perspective; more rooms make random assignments easier, but can make the test less challenging.

Note that there are **25 course subjects overall**: five subjects per semester, two sessions per group per subject, hence 10 weekly 2-hour lessons per group. There are **not 25 subjects per group**. Increasing to 25 subjects per group would require increasing timeslots or changing the load assumptions; the current 20 slots could not fit even one session of each subject per group.

To test an alternative dataset without modifying the default dataset:

```python
from hill_climbing_timetable import load_dataset, hill_climbing_search, display_results
sessions, rooms, slots = load_dataset('data_20_rooms.json')
result = hill_climbing_search(sessions, rooms, slots)
display_results(result, sessions)
```

