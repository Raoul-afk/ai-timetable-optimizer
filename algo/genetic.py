import json
import random
import time

def load_dataset(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    sessions = []
    for course in data["courses"]:
        semester = course["semester"]
        for g in range(1, data["groups_per_semester"] + 1):
            group = f"S{semester}_G{g}"
            for s_idx in range(1, course["sessions"] + 1):
                sessions.append({
                    "course_id": course["id"], "semester": semester,
                    "teacher": course["teacher"], "group": group
                })
    return sessions, data["rooms"], data["timeslots"]

def count_pairs(counter):
    return sum(n * (n - 1) // 2 for n in counter.values() if n > 1)

def cost(schedule, sessions_meta):
    r, g, t = {}, {}, {}
    for idx, (room, slot) in enumerate(schedule):
        meta = sessions_meta[idx]
        r[(room, slot)] = r.get((room, slot), 0) + 1
        g[(meta["group"], slot)] = g.get((meta["group"], slot), 0) + 1
        t[(meta["teacher"], slot)] = t.get((meta["teacher"], slot), 0) + 1
    return count_pairs(r) + count_pairs(g) + count_pairs(t)

def fitness(schedule, sessions_meta):
    return -cost(schedule, sessions_meta)

def tournament_selection(population, fits, k=5):
    # Un tournoi de taille 5 pour une pression sélective plus forte
    indices = random.sample(range(len(population)), k)
    best_idx = max(indices, key=lambda i: fits[i])
    return population[best_idx]

def uniform_crossover(p1, p2):
    c1, c2 = [], []
    for a, b in zip(p1, p2):
        if random.random() < 0.5:
            c1.append(a); c2.append(b)
        else:
            c1.append(b); c2.append(a)
    return c1, c2

def mutate(schedule, rooms, timeslots, gene_mutation_prob=0.02):
    new_sched = list(schedule)
    for i in range(len(new_sched)):
        if random.random() < gene_mutation_prob:
            r, t = new_sched[i]
            # On change soit la salle, soit le créneau (pas les deux, pour être plus précis)
            if random.random() < 0.5:
                new_sched[i] = (random.choice(rooms), t)
            else:
                new_sched[i] = (r, random.choice(timeslots))
    return new_sched

def run_pure_ga():
    print("Lancement du GA PUR (sans réparation, avec croisement uniforme)...")
    sessions_meta, rooms, timeslots = load_dataset("data/data_20_rooms.json")
    
    pop_size = 100
    generations = 1500
    
    # Population initiale
    population = [[(random.choice(rooms), random.choice(timeslots)) for _ in sessions_meta] for _ in range(pop_size)]
    fits = [fitness(ind, sessions_meta) for ind in population]
    
    best_overall_conf = -max(fits)
    t0 = time.time()

    for gen in range(generations):
        # Élitisme strict : on garde les 5 meilleurs
        order = sorted(range(pop_size), key=lambda i: fits[i], reverse=True)
        new_pop = [list(population[i]) for i in order[:5]]
        
        while len(new_pop) < pop_size:
            p1 = tournament_selection(population, fits, k=5)
            p2 = tournament_selection(population, fits, k=5)
            c1, c2 = uniform_crossover(p1, p2)
            
            # On mute les enfants
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
            print(f"  [Génération {gen:04d}] Nouveau record : {best_overall_conf} conflits")
            
            if best_overall_conf == 0:
                print(f"✨ Victoire du GA PUR à la génération {gen} ! (Temps : {time.time()-t0:.2f}s)")
                break
                
        elif gen % 100 == 0 and gen > 0:
            print(f"  [Génération {gen:04d}] Stagnation... (Record actuel : {best_overall_conf} conflits)")

    print("\nFin de l'exécution.")

if __name__ == "__main__":
    run_pure_ga()
