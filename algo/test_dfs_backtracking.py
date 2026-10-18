"""Small correctness checks; run: python -m unittest test_dfs_backtracking.py"""
import unittest
from dfs_backtracking_timetable import backtracking_search
from hill_climbing_timetable import compute_heuristic, load_dataset


class TimetableTests(unittest.TestCase):
    def test_shared_dataset(self):
        sessions, rooms, slots = load_dataset("data_hard.json")
        result = backtracking_search(sessions, rooms, slots, max_seconds=5)
        self.assertEqual(result["status"], "FEASIBLE")
        self.assertEqual(len(result["schedule"]), len(sessions))
        cost, _ = compute_heuristic(
            result["schedule"], {s["id"]: s for s in sessions}
        )
        self.assertEqual(cost, 0)

    def test_same_teacher_different_groups_cannot_overlap(self):
        sessions = [
            {"id": "s1", "group": "S5_G1", "teacher": "T1", "semester": 5, "course_id": "C1"},
            {"id": "s2", "group": "S5_G2", "teacher": "T1", "semester": 5, "course_id": "C1"},
        ]
        result = backtracking_search(sessions, ["R1", "R2"], ["MON_08", "MON_10"])
        self.assertEqual(result["status"], "FEASIBLE")
        self.assertNotEqual(result["schedule"]["s1"]["timeslot"], result["schedule"]["s2"]["timeslot"])

    def test_different_groups_and_teachers_may_overlap(self):
        sessions = [
            {"id": "s1", "group": "S5_G1", "teacher": "T1", "semester": 5, "course_id": "C1"},
            {"id": "s2", "group": "S5_G2", "teacher": "T2", "semester": 5, "course_id": "C2"},
        ]
        result = backtracking_search(sessions, ["R1", "R2"], ["MON_08"])
        self.assertEqual(result["status"], "FEASIBLE")
        self.assertEqual(result["schedule"]["s1"]["timeslot"], result["schedule"]["s2"]["timeslot"])
        self.assertNotEqual(result["schedule"]["s1"]["room"], result["schedule"]["s2"]["room"])

    def test_no_solution_if_one_teacher_needs_two_sessions_in_one_slot(self):
        sessions = [
            {"id": "s1", "group": "G1", "teacher": "T1", "course_id": "C1"},
            {"id": "s2", "group": "G2", "teacher": "T1", "course_id": "C1"},
        ]
        result = backtracking_search(sessions, ["R1", "R2"], ["MON_08"])
        self.assertEqual(result["status"], "NO_SOLUTION")
        self.assertIsNone(result["schedule"])

    def test_room_limit(self):
        sessions = [
            {"id": "s1", "group": "G1", "teacher": "T1", "course_id": "C1"},
            {"id": "s2", "group": "G2", "teacher": "T2", "course_id": "C2"},
        ]
        result = backtracking_search(sessions, ["R1"], ["MON_08"])
        self.assertEqual(result["status"], "NO_SOLUTION")


if __name__ == "__main__":
    unittest.main()
