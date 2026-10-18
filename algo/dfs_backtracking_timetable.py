"""University timetabling: DFS + Backtracking + MRV + Degree Heuristic.

Uses the SAME ``data_hard.json``, session expansion and fitness function
as ``hill_climbing_timetable.py``. Run both scripts from the same folder.

Hard constraints (single 2-hour timeslot per session):
* A room cannot hold two sessions simultaneously.
* A group cannot attend two sessions simultaneously.
* A teacher cannot teach two sessions simultaneously.

Different groups of the same semester may attend *different* courses at
one time. Each course has one teacher shared across its groups.

All rooms are interchangeable in the current dataset. For any valid slot,
we assign the first available room; exploring all other free rooms would
only generate symmetric (equivalent) solutions. The search is exhaustive
for this model, as long as the optional search limits are not reached.
"""

import argparse
import csv
import json
import time
from collections import defaultdict
from pathlib import Path

from hill_climbing_timetable import compute_heuristic, load_dataset


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "data_15_rooms.json"


def build_conflict_graph(sessions):
    """Neighbors share a group or a teacher (count each other session once)."""
    by_group = defaultdict(set)
    by_teacher = defaultdict(set)
    for session in sessions:
        by_group[session["group"]].add(session["id"])
        by_teacher[session["teacher"]].add(session["id"])

    graph = {}
    for session in sessions:
        sid = session["id"]
        graph[sid] = (
            by_group[session["group"]] | by_teacher[session["teacher"]]
        ) - {sid}
    return graph


def backtracking_search(
    sessions,
    rooms,
    timeslots,
    *,
    use_mrv=True,
    use_degree=True,
    max_seconds=30.0,
    max_nodes=2_000_000,
):
    """Search for a complete, conflict-free timetable.

    MRV counts currently available TIMESLOTS, not (timeslot, room) pairs:
    all rooms are interchangeable, and a slot is available when the group
    and teacher are free and at least one room remains.

    Returns the same result field ``schedule`` as the HC implementation,
    plus DFS-specific metrics. Returns ``None`` in schedule on failure.
    """
    if not sessions:
        return {
            "status": "FEASIBLE", "schedule": {}, "best_h": 0,
            "room_conflicts": 0, "group_conflicts": 0,
            "teacher_conflicts": 0, "same_course_conflicts": 0,
            "time_seconds": 0.0, "nodes_explored": 0,
            "backtracks": 0, "domain_checks": 0,
        }
    if not rooms or not timeslots:
        raise ValueError("The dataset must have at least one room and one timeslot.")

    by_id = {session["id"]: session for session in sessions}
    if len(by_id) != len(sessions):
        raise ValueError("Duplicate session IDs in dataset.")

    graph = build_conflict_graph(sessions)
    unassigned = set(by_id)
    schedule = {}
    busy_groups = set()    # (group, slot)
    busy_teachers = set()  # (teacher, slot)
    busy_rooms = {slot: set() for slot in timeslots}

    nodes = 0
    backtracks = 0
    domain_checks = 0
    limit_reached = False
    start = time.perf_counter()

    # Retain input order to ensure deterministic tie-breaking in MRV/degree.
    session_ids = [session["id"] for session in sessions]

    def available_slots(sid):
        """Check all current hard constraints for a particular session."""
        nonlocal domain_checks
        session = by_id[sid]
        group, teacher = session["group"], session["teacher"]
        available = []
        for slot in timeslots:
            domain_checks += 1
            if (group, slot) in busy_groups:
                continue
            if (teacher, slot) in busy_teachers:
                continue
            if len(busy_rooms[slot]) == len(rooms):
                continue
            available.append(slot)
        return available

    def choose_next_session():
        """MRV first; break ties by the largest degree among UNASSIGNED."""
        best_id, best_domain, best_key = None, None, None
        for sid in session_ids:
            if sid not in unassigned:
                continue
            domain = available_slots(sid)
            # Traditional MRV = minimum domain size.
            mrv = len(domain) if use_mrv else 0
            # Degree ties: prefer sessions constraining more unassigned ones.
            degree = len(graph[sid] & unassigned) if use_degree else 0
            key = (mrv, -degree)
            if best_key is None or key < best_key:
                best_id, best_domain, best_key = sid, domain, key
                if use_mrv and mrv == 0:
                    break
        return best_id, best_domain

    def dfs():
        nonlocal nodes, backtracks, limit_reached
        if not unassigned:
            return True
        if (max_seconds is not None and
                time.perf_counter() - start >= max_seconds):
            limit_reached = True
            return False
        if max_nodes is not None and nodes >= max_nodes:
            limit_reached = True
            return False

        sid, domain = choose_next_session()
        if not domain:
            # Forward checking: an unassigned session has no legal slot.
            backtracks += 1
            return False

        session = by_id[sid]
        group, teacher = session["group"], session["teacher"]

        for slot in domain:
            if (max_seconds is not None and
                    time.perf_counter() - start >= max_seconds):
                limit_reached = True
                return False
            if max_nodes is not None and nodes >= max_nodes:
                limit_reached = True
                return False

            # Every room is equivalent: choose the first one still free.
            room = next((r for r in rooms if r not in busy_rooms[slot]), None)
            if room is None:
                continue

            nodes += 1
            schedule[sid] = {"room": room, "timeslot": slot}
            unassigned.remove(sid)
            busy_groups.add((group, slot))
            busy_teachers.add((teacher, slot))
            busy_rooms[slot].add(room)

            if dfs():
                return True

            # Backtrack: roll back EXACTLY the state of this branch.
            busy_rooms[slot].remove(room)
            busy_teachers.remove((teacher, slot))
            busy_groups.remove((group, slot))
            unassigned.add(sid)
            del schedule[sid]

            if limit_reached:
                return False

        backtracks += 1
        return False

    solved = dfs()
    elapsed = time.perf_counter() - start
    if solved:
        cost, breakdown = compute_heuristic(schedule, by_id)
        assert cost == 0, f"Internal bug: invalid schedule, cost={cost}"
        status = "FEASIBLE"
    else:
        cost, breakdown = None, {
            "room_conflicts": None,
            "group_conflicts": None,
            "teacher_conflicts": None,
            "same_course_conflicts": None,
        }
        status = "SEARCH_LIMIT" if limit_reached else "NO_SOLUTION"

    return {
        "status": status,
        "time_seconds": round(elapsed, 4),
        "nodes_explored": nodes,
        "backtracks": backtracks,
        "domain_checks": domain_checks,
        "best_h": cost,
        **breakdown,
        "schedule": schedule.copy() if solved else None,
    }


def save_schedule_csv(output_path, result, sessions):
    """Export the same timetable information as HC, one row per session."""
    if result["schedule"] is None:
        raise ValueError("No complete schedule to export.")
    info_by_id = {s["id"]: s for s in sessions}
    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "session_id", "course_id", "course_name", "semester",
            "group", "teacher", "timeslot", "room",
        ])
        for sid, alloc in sorted(
            result["schedule"].items(),
            key=lambda x: (x[1]["timeslot"], x[1]["room"], x[0]),
        ):
            s = info_by_id[sid]
            writer.writerow([
                sid, s["course_id"], s["course_name"], s["semester"],
                s["group"], s["teacher"], alloc["timeslot"], alloc["room"],
            ])


def main():
    parser = argparse.ArgumentParser(
        description="DFS + Backtracking + MRV + Degree for university timetable"
    )
    parser.add_argument("--dataset", type=Path, default=DATA_FILE)
    parser.add_argument("--output", type=Path, default=Path("dfs_schedule.csv"))
    parser.add_argument("--max-seconds", type=float, default=30.0)
    parser.add_argument("--max-nodes", type=int, default=2_000_000)
    parser.add_argument("--no-mrv", action="store_true",
                        help="disable MRV (for ablation tests)")
    parser.add_argument("--no-degree", action="store_true",
                        help="disable degree tie breaker (for ablation tests)")
    args = parser.parse_args()

    sessions, rooms, timeslots = load_dataset(args.dataset)
    print(f"Dataset: {args.dataset}")
    print(f"Sessions: {len(sessions)} | Groups: {len(set(s['group'] for s in sessions))} "
          f"| Rooms: {len(rooms)} | Timeslots: {len(timeslots)}")
    result = backtracking_search(
        sessions, rooms, timeslots,
        use_mrv=not args.no_mrv,
        use_degree=not args.no_degree,
        max_seconds=args.max_seconds,
        max_nodes=args.max_nodes,
    )

    print("\nDFS + BACKTRACKING REPORT")
    for key in (
        "status", "time_seconds", "nodes_explored", "backtracks",
        "domain_checks", "best_h", "room_conflicts",
        "group_conflicts", "teacher_conflicts", "same_course_conflicts",
    ):
        print(f"{key:<24}: {result[key]}")

    if result["schedule"] is not None:
        save_schedule_csv(args.output, result, sessions)
        print(f"\nTimetable saved to: {args.output}")
    else:
        print("\nNo complete timetable exported. "
              "SEARCH_LIMIT means the solver did NOT prove infeasibility.")


if __name__ == "__main__":
    main()
