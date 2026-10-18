import json
import random
import time

def load_dataset(filepath):
    """Loads the dataset and generates all individual sessions for each group."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    sessions = []
    for course in data["courses"]:
        semester = course["semester"]
        for g in range(1, data["groups_per_semester"] + 1):
            group = f"S{semester}_G{g}"
            for s_idx in range(1, course["sessions"] + 1):
                sessions.append({
                    "id": f"{course['id']}_{group}_s{s_idx}",
                    "course_id": course["id"],
                    "course_name": course["name"],
                    "semester": semester,
                    "teacher": course["teacher"],
                    "group": group
                })
    return sessions, data["rooms"], data["timeslots"]

def count_pairs(counter):
    """Calculates the exact number of colliding pairs."""
    return sum(n * (n - 1) // 2 for n in counter.values() if n > 1)

def cost(schedule, sessions_meta):
    """Calculates the total number of hard constraint violations."""
    r, g, t = {}, {}, {}
    for idx, (room, slot) in enumerate(schedule):
        meta = sessions_meta[idx]
        r[(room, slot)] = r.get((room, slot), 0) + 1
        g[(meta["group"], slot)] = g.get((meta["group"], slot), 0) + 1
        t[(meta["teacher"], slot)] = t.get((meta["teacher"], slot), 0) + 1
    return count_pairs(r) + count_pairs(g) + count_pairs(t)

def fitness(schedule, sessions_meta):
    """Returns a negative score. Closer to 0 is better."""
    return -cost(schedule, sessions_meta)

def tournament_selection(population, fits, k=5):
    """Selects the best individual among 'k' randomly chosen ones."""
    indices = random.sample(range(len(population)), k)
    best_idx = max(indices, key=lambda i: fits[i])
    return population[best_idx]

def uniform_crossover(p1, p2):
    """Uniform crossover: each gene is randomly taken from one of the parents."""
    c1, c2 = [], []
    for a, b in zip(p1, p2):
        if random.random() < 0.5:
            c1.append(a); c2.append(b)
        else:
            c1.append(b); c2.append(a)
    return c1, c2

def mutate(schedule, rooms, timeslots, gene_mutation_prob=0.02):
    """Mutates specific genes by changing either the room or the timeslot."""
    new_sched = list(schedule)
    for i in range(len(new_sched)):
        if random.random() < gene_mutation_prob:
            r, t = new_sched[i]
            if random.random() < 0.5:
                new_sched[i] = (random.choice(rooms), t)
            else:
                new_sched[i] = (r, random.choice(timeslots))
    return new_sched

def run_pure_ga(sessions_meta, rooms, timeslots, pop_size=100, generations=1500):
    """Runs the pure Genetic Algorithm."""
    # Initial population
    population = [[(random.choice(rooms), random.choice(timeslots)) for _ in sessions_meta] for _ in range(pop_size)]
    fits = [fitness(ind, sessions_meta) for ind in population]
    
    best_overall_conf = -max(fits)
    best_schedule = population[fits.index(max(fits))]
    t0 = time.time()

    for gen in range(generations):
        # Strict elitism: keep the top 5
        order = sorted(range(pop_size), key=lambda i: fits[i], reverse=True)
        new_pop = [list(population[i]) for i in order[:5]]
        
        while len(new_pop) < pop_size:
            p1 = tournament_selection(population, fits, k=5)
            p2 = tournament_selection(population, fits, k=5)
            c1, c2 = uniform_crossover(p1, p2)
            
            c1 = mutate(c1, rooms, timeslots, gene_mutation_prob=0.02)
            c2 = mutate(c2, rooms, timeslots, gene_mutation_prob=0.02)
            
            new_pop.append(c1)
            if len(new_pop) < pop_size:
                new_pop.append(c2)
                
        population = new_pop
        fits = [fitness(ind, sessions_meta) for ind in population]
        
        current_best_conf = -max(fits)
        
        if current_best_conf < best_overall_conf:
            best_overall_conf = current_best_conf
            best_schedule = population[fits.index(max(fits))]
            
            if best_overall_conf == 0:
                break

    return best_schedule, best_overall_conf

def display_results(schedule, sessions_meta, rooms, timeslots, execution_time):
    """Displays the final schedule in a clean tabular format."""
    print("\nEXECUTION REPORT\n")
    print(f"{'Execution time':<25}: {execution_time:.4f} s")
    print(f"{'Remaining conflicts':<25}: {cost(schedule, sessions_meta)}")
    
    print("\nGENERATED SCHEDULE\n")
    print(f"{'Slot':<8} | {'Room':<5} | {'Group':<6} | {'Course':<26} | {'Teacher':<7}")
    print("-" * 75)
    
    # Build a sortable list of tuples
    formatted_schedule = []
    for idx, (room, slot) in enumerate(schedule):
        meta = sessions_meta[idx]
        formatted_schedule.append((slot, room, meta["group"], meta["course_name"], meta["teacher"]))
        
    # Sort by slot first, then room
    formatted_schedule.sort(key=lambda x: (x[0], x[1]))
    
    for slot, room, group, course_name, teacher in formatted_schedule:
        print(f"{slot:<8} | {room:<5} | {group:<6} | {course_name[:26]:<26} | {teacher:<7}")

if __name__ == "__main__":
    # Load data (update the path if necessary)
    filepath = "data/data_20_rooms.json"
    sessions_meta, rooms, timeslots = load_dataset(filepath)
    
    print("Running Genetic Algorithm... (this may take a few seconds)")
    start_time = time.time()
    
    # Run GA
    best_schedule, _ = run_pure_ga(sessions_meta, rooms, timeslots)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Display
    display_results(best_schedule, sessions_meta, rooms, timeslots, execution_time)
