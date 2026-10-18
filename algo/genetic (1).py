import json
import random
import time

def load_dataset(filepath):
    """Charge le dataset JSON et génère toutes les sessions individuelles pour chaque groupe."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    rooms = data["rooms"]
    timeslots = data["timeslots"]
    groups_per_sem = data["groups_per_semester"]
    
    # Construction de la liste exhaustive de toutes les sessions à planifier
    # Chaque cours a un nombre de sessions hebdomadaires par groupe.
    # Il y a 4 groupes par semestre (ex: S1_G1, S1_G2, S1_G3, S1_G4).
    sessions_to_schedule = []
    
    for course in data["courses"]:
        course_id = course["id"]
        semester = course["semester"]
        teacher = course["teacher"]
        num_sessions = course["sessions"]
        
        # Création des groupes pour ce semestre
        groups = [f"S{semester}_G{g}" for g in range(1, groups_per_sem + 1)]
        
        for group in groups:
            for s_idx in range(1, num_sessions + 1):
                session_info = {
                    "course_id": course_id,
                    "semester": semester,
                    "teacher": teacher,
                    "group": group,
                    "session_index": s_idx
                }
                sessions_to_schedule.append(session_info)
                
    return sessions_to_schedule, rooms, timeslots

def cost(schedule, sessions_meta):
    """
    Calcule le nombre de violations des contraintes dures :
    1. Même (salle, créneau) pour plusieurs sessions.
    2. Même (groupe, créneau) pour plusieurs sessions.
    3. Même (enseignant, créneau) pour plusieurs sessions.
    """
    room_conflicts = {}
    group_conflicts = {}
    teacher_conflicts = {}
    
    for idx, (room, slot) in enumerate(schedule):
        meta = sessions_meta[idx]
        group = meta["group"]
        teacher = meta["teacher"]
        
        # Clés de suivi des ressources par créneau
        r_key = (room, slot)
        g_key = (group, slot)
        t_key = (teacher, slot)
        
        room_conflicts[r_key] = room_conflicts.get(r_key, 0) + 1
        group_conflicts[g_key] = group_conflicts.get(g_key, 0) + 1
        teacher_conflicts[t_key] = teacher_conflicts.get(t_key, 0) + 1
        
    total_conflicts = 0
    # Chaque affectation excédentaire sur une ressource au même timeslot compte comme un conflit
    for count in room_conflicts.values():
        if count > 1:
            total_conflicts += count - 1
    for count in group_conflicts.values():
        if count > 1:
            total_conflicts += count - 1
    for count in teacher_conflicts.values():
        if count > 1:
            total_conflicts += count - 1
            
    return total_conflicts

def fitness(schedule, sessions_meta):
    c = cost(schedule, sessions_meta)
    return 1.0 / (1.0 + c)

def run_genetic_algorithm_dataset(json_path="data_20_rooms.json", pop_size=100, generations=1000, elite_size=2, mutation_rate=0.1, gene_mutation_prob=0.1):
    sessions_meta, rooms, timeslots = load_dataset(json_path)
    
    # (a) Population initiale : chaque individu est une liste de tuples (room, timeslot) pour chaque session
    population = [
        [(random.choice(rooms), random.choice(timeslots)) for _ in sessions_meta]
        for _ in range(pop_size)
    ]
    
    for g in range(generations):
        fits = [fitness(ind, sessions_meta) for ind in population]
        
        if max(fits) == 1.0:
            best_idx = fits.index(max(fits))
            print(f"✨ Solution parfaite trouvée à la génération {g} !")
            return population[best_idx], sessions_meta, rooms, timeslots, g
            
        paired = list(zip(population, fits))
        paired.sort(key=lambda x: x[1], reverse=True)
        elites = [ind for ind, f in paired[:elite_size]]
        
        total_fit = sum(fits)
        probabilities = [f / total_fit for f in fits] if total_fit > 0 else [1.0/pop_size]*pop_size
        
        new_population = list(elites)
        
        while len(new_population) < pop_size:
            parent1, parent2 = random.choices(population, weights=probabilities, k=2)
            
            # Croisement en un point
            pt = random.randint(1, len(sessions_meta) - 1)
            child1 = parent1[:pt] + parent2[pt:]
            child2 = parent2[:pt] + parent1[pt:]
            
            # Mutation de l'enfant 1
            if random.random() < mutation_rate:
                child1 = [
                    (random.choice(rooms), random.choice(timeslots)) if random.random() < gene_mutation_prob else (r, s)
                    for r, s in child1
                ]
            # Mutation de l'enfant 2
            if random.random() < mutation_rate:
                child2 = [
                    (random.choice(rooms), random.choice(timeslots)) if random.random() < gene_mutation_prob else (r, s)
                    for r, s in child2
                ]
                
            new_population.append(child1)
            if len(new_population) < pop_size:
                new_population.append(child2)
                
        population = new_population
        
    fits = [fitness(ind, sessions_meta) for ind in population]
    best_idx = fits.index(max(fits))
    return population[best_idx], sessions_meta, rooms, timeslots, generations

# --- EXÉCUTION ---
if __name__ == "__main__":
    best_sched, sessions_meta, rooms, timeslots, nb_gens = run_genetic_algorithm_dataset(json_path="data_20_rooms.json")
    print(f"Conflits restants : {cost(best_sched, sessions_meta)}")
    print("\nAperçu des 10 premières affectations de l'emploi du temps :")
    for idx, (room, slot) in enumerate(best_sched[:10]):
        meta = sessions_meta[idx]
        print(f"Cours : {meta['course_id']} | Groupe : {meta['group']} | Prof : {meta['teacher']} -> Salle {room}, Créneau {slot}")
