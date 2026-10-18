"""Timetable generator: stochastic hill climbing + random walk + random restarts.

Each lesson is a 2-hour block. The `sessions` field in data_hard.json
represents the number of lessons of a subject PER GROUP each week.

Hard constraints:
 - no room hosts multiple sessions in one slot;
 - no group attends two sessions in one slot;
 - no teacher teaches two sessions in one slot.

There is deliberately NO conflict on the semester alone: distinct groups
in S5 can attend different subjects simultaneously.
"""

import json
import random
import time
from collections import Counter
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "data_20_rooms.json"


def load_dataset(filepath=DATA_FILE):
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    sessions = []
    for course in data["courses"]:
        sem = course["semester"]
        for group_number in range(1, data["groups_per_semester"] + 1):
            group_id = f"S{sem}_G{group_number}"
            for session_number in range(1, course["sessions"] + 1):
                sessions.append({
                    "id": f"{course['id']}_{group_id}_s{session_number}",
                    "course_id": course["id"],
                    "course_name": course["name"],
                    "semester": sem,
                    "group": group_id,
                    "teacher": course["teacher"],
                })
    return sessions, data["rooms"], data["timeslots"]


def generate_initial_state(sessions, rooms, timeslots):
    return {
        session["id"]: {
            "room": random.choice(rooms),
            "timeslot": random.choice(timeslots),
        }
        for session in sessions
    }


def count_pairs(counter):
    """Number of colliding PAIRS, e.g. 3 lessons together -> 3 conflicts."""
    return sum(n * (n - 1) // 2 for n in counter.values())


def compute_heuristic(state, session_lookup):
    by_room = Counter()
    by_group = Counter()
    by_teacher = Counter()
    by_course = Counter()  # For reporting, NOT added twice to fitness.

    for session_id, assignment in state.items():
        room, slot = assignment["room"], assignment["timeslot"]
        if room is None or slot is None:
            continue
        info = session_lookup[session_id]
        by_room[(room, slot)] += 1
        by_group[(info["group"], slot)] += 1
        by_teacher[(info["teacher"], slot)] += 1
        by_course[(info["course_id"], slot)] += 1

    breakdown = {
        "room_conflicts": count_pairs(by_room),
        "group_conflicts": count_pairs(by_group),
        "teacher_conflicts": count_pairs(by_teacher),
        # Teacher is unique to each subject, so this is already covered by teacher_conflicts.
        "same_course_conflicts": count_pairs(by_course),
    }
    total = sum(breakdown[key] for key in ("room_conflicts", "group_conflicts", "teacher_conflicts"))
    return total, breakdown


def get_random_neighbor(state, sessions, rooms, timeslots):
    # Shallow copy is safe because each replacement assignment dict is also copied.
    neighbor = state.copy()
    chosen_id = random.choice(sessions)["id"]
    old = state[chosen_id]
    # Try not to return exactly the same assignment as before.
    new_room = random.choice(rooms)
    new_slot = random.choice(timeslots)
    if len(rooms) * len(timeslots) > 1:
        while new_room == old["room"] and new_slot == old["timeslot"]:
            new_room = random.choice(rooms)
            new_slot = random.choice(timeslots)
    neighbor[chosen_id] = {"room": new_room, "timeslot": new_slot}
    return neighbor


def get_best_neighbor(state, sessions, rooms, timeslots, session_lookup, sample_size=35):
    best_state, best_cost = None, float("inf")
    for _ in range(sample_size):
        neighbor = get_random_neighbor(state, sessions, rooms, timeslots)
        cost, _ = compute_heuristic(neighbor, session_lookup)
        if cost < best_cost:
            best_state, best_cost = neighbor, cost
    return best_state, best_cost


def hill_climbing_search(
    sessions,
    rooms,
    timeslots,
    *,
    max_restarts=5,
    max_steps=300,
    p_greedy=0.85,
    sample_size=35,
    seed=42,
):
    random.seed(seed)
    session_lookup = {session["id"]: session for session in sessions}
    best_overall_state = None
    best_overall_h = float("inf")
    total_evals = 0
    restarts_used = 0
    start_time = time.perf_counter()

    for restart in range(1, max_restarts + 1):
        restarts_used = restart
        current_state = generate_initial_state(sessions, rooms, timeslots)
        current_h, _ = compute_heuristic(current_state, session_lookup)
        total_evals += 1

        if current_h < best_overall_h:
            best_overall_h = current_h
            best_overall_state = current_state.copy()

        for _ in range(max_steps):
            if current_h == 0:
                break

            if random.random() < p_greedy:
                next_state, next_h = get_best_neighbor(
                    current_state, sessions, rooms, timeslots,
                    session_lookup, sample_size=sample_size
                )
                total_evals += sample_size  # Count every candidate evaluated.
                if next_h <= current_h:
                    current_state, current_h = next_state, next_h
            else:
                # Random Walk: even a worse neighbor is accepted.
                next_state = get_random_neighbor(current_state, sessions, rooms, timeslots)
                next_h, _ = compute_heuristic(next_state, session_lookup)
                total_evals += 1
                current_state, current_h = next_state, next_h

            if current_h < best_overall_h:
                best_overall_h = current_h
                best_overall_state = current_state.copy()

        if best_overall_h == 0:
            break

    elapsed_time = time.perf_counter() - start_time
    _, breakdown = compute_heuristic(best_overall_state, session_lookup)
    return {
        "status": "FEASIBLE" if best_overall_h == 0 else "CONFLICTS_REMAIN",
        "time_seconds": round(elapsed_time, 4),
        "total_evaluations": total_evals,
        "restarts_used": restarts_used,
        "best_h": best_overall_h,
        **breakdown,
        "schedule": best_overall_state,
    }


def display_results(results, sessions):
    lookup = {session["id"]: session for session in sessions}
    print("\nEXECUTION REPORT\n")
    for key in (
        "status", "time_seconds", "total_evaluations", "restarts_used", "best_h",
        "room_conflicts", "group_conflicts", "teacher_conflicts", "same_course_conflicts"
    ):
        print(f"{key:<25}: {results[key]}")
    print("\nGENERATED SCHEDULE\n")
    print(f"{'Slot':<8} | {'Room':<5} | {'Group':<6} | {'Course':<26} | {'Teacher':<7}")
    print("-" * 75)
    for session_id, alloc in sorted(
        results["schedule"].items(),
        key=lambda pair: (pair[1]["timeslot"], pair[1]["room"], pair[0])
    ):
        info = lookup[session_id]
        print(
            f"{alloc['timeslot']:<8} | {alloc['room']:<5} | "
            f"{info['group']:<6} | {info['course_name'][:26]:<26} | {info['teacher']:<7}"
        )


if __name__ == "__main__":
    sessions, rooms, timeslots = load_dataset()
    print(f"Sessions: {len(sessions)}, groups: {len(set(s['group'] for s in sessions))}, rooms: {len(rooms)}")
    results = hill_climbing_search(sessions, rooms, timeslots)
    display_results(results, sessions)
