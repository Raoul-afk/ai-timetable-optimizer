import json
import random
import time

DATA_FILE = "data_hard.json"


def load_dataset(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    sessions = []
    for c in data["courses"]:
        for s_idx in range(1, c["sessions"] + 1):
            sessions.append({
                "id": f"{c['id']}_s{s_idx}",
                "course_id": c["id"],
                "semester": c["semester"]
            })

    return sessions, data["rooms"], data["timeslots"]


def generate_initial_state(sessions, rooms, timeslots):
    state = {}
    for s in sessions:
        state[s["id"]] = {
            "room": random.choice(rooms),
            "timeslot": random.choice(timeslots),
            "semester": s["semester"]
        }
    return state


def compute_heuristic(state):
    room_conflicts = 0
    semester_conflicts = 0
    room_slot_map = {}
    sem_slot_map = {}

    for item in state.values():
        if item["room"] is None or item["timeslot"] is None:
            continue

        r_key = (item["room"], item["timeslot"])
        s_key = (item["semester"], item["timeslot"])

        room_slot_map[r_key] = room_slot_map.get(r_key, 0) + 1
        sem_slot_map[s_key] = sem_slot_map.get(s_key, 0) + 1

    for count in room_slot_map.values():
        if count > 1:
            room_conflicts += count * (count - 1) // 2

    for count in sem_slot_map.values():
        if count > 1:
            semester_conflicts += count * (count - 1) // 2

    return (room_conflicts + semester_conflicts), room_conflicts, semester_conflicts


def get_random_neighbor(state, sessions, rooms, timeslots):
    neighbor = {k: dict(v) for k, v in state.items()}
    chosen_id = random.choice(sessions)["id"]
    neighbor[chosen_id]["room"] = random.choice(rooms)
    neighbor[chosen_id]["timeslot"] = random.choice(timeslots)
    return neighbor


def get_best_neighbor(state, sessions, rooms, timeslots, sample_size=35):
    best_state = None
    best_h = float("inf")

    for _ in range(sample_size):
        neighbor = get_random_neighbor(state, sessions, rooms, timeslots)
        h, _, _ = compute_heuristic(neighbor)
        if h < best_h:
            best_h = h
            best_state = neighbor

    return best_state, best_h


def hill_climbing_search(sessions, rooms, timeslots, max_restarts=15, max_steps=500, p_greedy=0.85):
    best_overall_state = None
    best_overall_h = float("inf")
    total_evals = 0

    start_time = time.time()

    for restart in range(1, max_restarts + 1):
        current_state = generate_initial_state(sessions, rooms, timeslots)
        current_h, _, _ = compute_heuristic(current_state)

        if current_h < best_overall_h:
            best_overall_h = current_h
            best_overall_state = current_state

        for step in range(1, max_steps + 1):
            total_evals += 1

            if current_h == 0:
                break

            # greedy move vs random walk
            if random.random() < p_greedy:
                next_state, next_h = get_best_neighbor(current_state, sessions, rooms, timeslots)
                if next_h <= current_h:
                    current_state = next_state
                    current_h = next_h
            else:
                next_state = get_random_neighbor(current_state, sessions, rooms, timeslots)
                next_h, _, _ = compute_heuristic(next_state)
                current_state = next_state
                current_h = next_h

            if current_h < best_overall_h:
                best_overall_h = current_h
                best_overall_state = current_state

        if best_overall_h == 0:
            break

    elapsed_time = time.time() - start_time
    _, r_conf, s_conf = compute_heuristic(best_overall_state)

    return {
        "status": "OPTIMAL" if best_overall_h == 0 else "SUBOPTIMAL",
        "time_seconds": round(elapsed_time, 4),
        "total_evaluations": total_evals,
        "restarts_used": restart,
        "best_h": best_overall_h,
        "room_conflicts": r_conf,
        "semester_conflicts": s_conf,
        "schedule": best_overall_state
    }


def display_results(results, all_sessions):
    print("\nEXECUTION REPORT\n")
    print(f"Status               : {results['status']}")
    print(f"Elapsed Time         : {results['time_seconds']} s")
    print(f"Restarts Completed   : {results['restarts_used']}")
    print(f"Evaluations Count    : {results['total_evaluations']}")
    print(f"Residual Conflicts   : {results['best_h']}")
    print(f" - Room overlap      : {results['room_conflicts']}")
    print(f" - Semester overlap  : {results['semester_conflicts']}")

    # detect unassigned sessions if any
    unplaced = []
    for s in all_sessions:
        alloc = results["schedule"].get(s["id"])
        if not alloc or alloc.get("room") is None or alloc.get("timeslot") is None:
            unplaced.append(s["id"])

    if unplaced:
        print(f"Unassigned Sessions ({len(unplaced)}): {', '.join(unplaced)}")
        print("-" * 48)

    print("\n\nGENERATED SCHEDULE\n\n")
    print(f"{'Session ID':<15} | {'Sem.':<5} | {'Room':<6} | {'Slot':<8}")
    print("------------------------------------------------")

    sorted_schedule = sorted(
        results["schedule"].items(),
        key=lambda x: (x[1]["timeslot"], x[1]["room"])
    )

    for session_id, alloc in sorted_schedule:
        sem_str = f"S{alloc['semester']}"
        room_str = alloc["room"] if alloc["room"] else "N/A"
        slot_str = alloc["timeslot"] if alloc["timeslot"] else "N/A"
        print(f"{session_id:<15} | {sem_str:<5} | {room_str:<6} | {slot_str:<8}")

    print("------------------------------------------------")


if __name__ == "__main__":
    sessions, rooms, timeslots = load_dataset(DATA_FILE)
    res = hill_climbing_search(sessions, rooms, timeslots)
    display_results(res, sessions)