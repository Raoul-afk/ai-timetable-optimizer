import time
import random
import statistics
import sys
import os

# 1. On récupère le dossier où se trouve ce script (le dossier "performance")
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. On remonte d'un niveau pour trouver la racine du projet
root_dir = os.path.dirname(current_dir)

# 3. On ajoute le dossier 'algo' au chemin de recherche de Python
sys.path.append(os.path.join(root_dir, "algo"))

# 4. On importe normalement, sans "algo."
from genetic import load_dataset as load_ga, run_pure_ga
from hill_climbing_timetable import load_dataset as load_hc, hill_climbing_search
from dfs_backtracking_timetable import backtracking_search

# 5. On définit les chemins vers les datasets en partant de la racine
DATASETS = [
    os.path.join(root_dir, "data", "data_20_rooms.json"),
    os.path.join(root_dir, "data", "data_15_rooms.json"),
    os.path.join(root_dir, "data", "data_12_rooms.json")
]

def run_benchmark_for_dataset(dataset_path, num_runs=5):
    print(f"\n{'='*70}")
    print(f"📊 BENCHMARKING DATASET: {dataset_path}")
    print(f"{'='*70}")

    # ==========================================
    # 1. GENETIC ALGORITHM
    # ==========================================
    print("Running Genetic Algorithm...")
    ga_times = []
    ga_conflicts = []
    
    for run in range(num_runs):
        random.seed(42 + run) 
        sessions, rooms, timeslots = load_ga(dataset_path)
        
        start = time.time()
        _, best_conf = run_pure_ga(sessions, rooms, timeslots)
        end = time.time()
        
        ga_times.append(end - start)
        ga_conflicts.append(best_conf)

    # ==========================================
    # 2. HILL CLIMBING
    # ==========================================
    print("Running Hill Climbing...")
    hc_times = []
    hc_conflicts = []
    
    for run in range(num_runs):
        sessions, rooms, timeslots = load_hc(dataset_path)
        
        start = time.time()
        result = hill_climbing_search(sessions, rooms, timeslots, seed=42 + run)
        end = time.time()
        
        hc_times.append(end - start)
        hc_conflicts.append(result["best_h"])

    # ==========================================
    # 3. DFS BACKTRACKING
    # ==========================================
    print("Running DFS + Backtracking...")
    dfs_times = []
    dfs_conflicts = []
    
    for run in range(num_runs):
        sessions, rooms, timeslots = load_hc(dataset_path) # On utilise load_hc qui est déjà importé
        
        start = time.time()
        result = backtracking_search(sessions, rooms, timeslots)
        end = time.time()
        
        dfs_times.append(end - start)
        # Si le DFS atteint la limite de temps sans trouver (None), on met 999
        dfs_conflicts.append(result["best_h"] if result["best_h"] is not None else 999)

    # ==========================================
    # AFFICHAGE DES RÉSULTATS POUR CE DATASET
    # ==========================================
    print(f"\n--- Results for {os.path.basename(dataset_path)} ---")
    print(f"{'Method':<20} | {'Success':<8} | {'Mean conflicts':<15} | {'Mean time (s)':<10}")
    print("-" * 65)
    
    ga_success = sum(1 for c in ga_conflicts if c == 0)
    ga_mean_c = statistics.mean(ga_conflicts)
    ga_mean_t = statistics.mean(ga_times)
    print(f"{'Genetic Algorithm':<20} | {ga_success}/{num_runs:<6} | {ga_mean_c:<15.1f} | {ga_mean_t:<10.3f}")
    
    hc_success = sum(1 for c in hc_conflicts if c == 0)
    hc_mean_c = statistics.mean(hc_conflicts)
    hc_mean_t = statistics.mean(hc_times)
    print(f"{'Hill Climbing':<20} | {hc_success}/{num_runs:<6} | {hc_mean_c:<15.1f} | {hc_mean_t:<10.3f}")
    
    dfs_success = sum(1 for c in dfs_conflicts if c == 0)
    dfs_mean_c = statistics.mean(dfs_conflicts)
    dfs_mean_t = statistics.mean(dfs_times)
    print(f"{'DFS + Backtracking':<20} | {dfs_success}/{num_runs:<6} | {dfs_mean_c:<15.1f} | {dfs_mean_t:<10.3f}")
    print("-" * 65)
    
    # Affichage pour le rapport
    print("\n--- COPY THIS FOR YOUR REPORT ---")
    print("| Method | Runs with 0 conflicts | Mean conflicts | Mean time | Time range |")
    print("| :--- | :--- | :--- | :--- | :--- |")
    print(f"| DFS + Backtracking | {dfs_success}/{num_runs} | {dfs_mean_c:.1f} | {dfs_mean_t:.3f} s | {min(dfs_times):.3f}–{max(dfs_times):.3f} s |")
    print(f"| Genetic Algorithm | {ga_success}/{num_runs} | {ga_mean_c:.1f} | {ga_mean_t:.3f} s | {min(ga_times):.3f}–{max(ga_times):.3f} s |")
    print(f"| Hill Climbing | {hc_success}/{num_runs} | {hc_mean_c:.1f} | {hc_mean_t:.3f} s | {min(hc_times):.3f}–{max(hc_times):.3f} s |")

if __name__ == "__main__":
    for ds in DATASETS:
        if os.path.exists(ds):
            run_benchmark_for_dataset(ds)
        else:
            print(f"\n⚠️ Fichier introuvable : {ds}. Vérifie le chemin.")
