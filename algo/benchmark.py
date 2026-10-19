import time
import random
import statistics
import sys
import os

# On ajoute le dossier 'algo' au chemin pour pouvoir importer tes fichiers
sys.path.append(os.path.join(os.path.dirname(__file__), 'algo'))

# Importation de tes 3 algorithmes
# (Assure-toi que les noms de fichiers correspondent exactement)
from genetic import load_dataset as load_ga, run_pure_ga
from hill_climbing_timetable import load_dataset as load_hc, hill_climbing_search
from dfs_backtracking_timetable import backtracking_search

def run_benchmark():
    dataset_path = "data/data_20_rooms.json"
    num_runs = 5
    
    print(f"--- Starting Benchmark on {dataset_path} ({num_runs} runs each) ---\n")

    # ==========================================
    # 1. GENETIC ALGORITHM
    # ==========================================
    print("Running Genetic Algorithm...")
    ga_times = []
    ga_conflicts = []
    
    for run in range(num_runs):
        # On change la seed à chaque run (42, 43, 44, 45, 46)
        random.seed(42 + run) 
        sessions, rooms, timeslots = load_ga(dataset_path)
        
        start = time.time()
        _, best_conf = run_pure_ga(sessions, rooms, timeslots)
        end = time.time()
        
        ga_times.append(end - start)
        ga_conflicts.append(best_conf)
        print(f"  Run {run+1}: {best_conf} conflicts, {end - start:.3f} s")

    # ==========================================
    # 2. HILL CLIMBING
    # ==========================================
    print("\nRunning Hill Climbing...")
    hc_times = []
    hc_conflicts = []
    
    for run in range(num_runs):
        sessions, rooms, timeslots = load_hc(dataset_path)
        
        start = time.time()
        # On lui passe une seed différente à chaque run
        result = hill_climbing_search(sessions, rooms, timeslots, seed=42 + run)
        end = time.time()
        
        hc_times.append(end - start)
        hc_conflicts.append(result["best_h"])
        print(f"  Run {run+1}: {result['best_h']} conflicts, {end - start:.3f} s")

    # ==========================================
    # 3. DFS BACKTRACKING
    # ==========================================
    print("\nRunning DFS + Backtracking...")
    dfs_times = []
    dfs_conflicts = []
    
    # Le DFS est déterministe, pas besoin de changer la seed
    for run in range(num_runs):
        # On recharge les données pour être sûr
        from hill_climbing_timetable import load_dataset as load_dfs
        sessions, rooms, timeslots = load_dfs(dataset_path)
        
        start = time.time()
        result = backtracking_search(sessions, rooms, timeslots)
        end = time.time()
        
        dfs_times.append(end - start)
        dfs_conflicts.append(result["best_h"] if result["best_h"] is not None else 999)
        print(f"  Run {run+1}: {result['best_h']} conflicts, {end - start:.3f} s")

    # ==========================================
    # AFFICHAGE DES RÉSULTATS
    # ==========================================
    print("\n" + "="*65)
    print(f"{'Method':<20} | {'Success':<8} | {'Mean conflicts':<15} | {'Mean time (s)':<10}")
    print("-" * 65)
    
    # Stats GA
    ga_success = sum(1 for c in ga_conflicts if c == 0)
    ga_mean_c = statistics.mean(ga_conflicts)
    ga_mean_t = statistics.mean(ga_times)
    print(f"{'Genetic Algorithm':<20} | {ga_success}/{num_runs:<6} | {ga_mean_c:<15.1f} | {ga_mean_t:<10.3f}")
    
    # Stats HC
    hc_success = sum(1 for c in hc_conflicts if c == 0)
    hc_mean_c = statistics.mean(hc_conflicts)
    hc_mean_t = statistics.mean(hc_times)
    print(f"{'Hill Climbing':<20} | {hc_success}/{num_runs:<6} | {hc_mean_c:<15.1f} | {hc_mean_t:<10.3f}")
    
    # Stats DFS
    dfs_success = sum(1 for c in dfs_conflicts if c == 0)
    dfs_mean_c = statistics.mean(dfs_conflicts)
    dfs_mean_t = statistics.mean(dfs_times)
    print(f"{'DFS + Backtracking':<20} | {dfs_success}/{num_runs:<6} | {dfs_mean_c:<15.1f} | {dfs_mean_t:<10.3f}")
    print("="*65)
    
    print(f"\nTime ranges:")
    print(f"  GA : {min(ga_times):.3f} – {max(ga_times):.3f} s")
    print(f"  HC : {min(hc_times):.3f} – {max(hc_times):.3f} s")
    print(f"  DFS: {min(dfs_times):.3f} – {max(dfs_times):.3f} s")

if __name__ == "__main__":
    run_benchmark()
