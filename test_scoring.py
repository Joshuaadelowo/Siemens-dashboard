import unittest

from data_loader import load_monthly_records
from scoring import (
    ABOVE_AVERAGE_SCORE_PENALTY,
    BELOW_AVERAGE_SCORE_BONUS,
    UPGRADE_SCORE_BONUS,
    Building,
    GameState,
    Rating,
    average_carbon_tonnes,
)


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.records = load_monthly_records()

    def test_average_matches_expected(self):
        self.assertAlmostEqual(average_carbon_tonnes(self.records), 74.18, places=1)

    def test_rejects_wrong_record_count(self):
        with self.assertRaises(ValueError):
            GameState(self.records[:5])

    def test_first_turn_below_average_no_upgrade(self):
        state = GameState(self.records)
        result = state.advance_turn()
        self.assertTrue(result.beat_average)  # Aug 2025 is below the 12-month average
        self.assertEqual(result.score_delta, BELOW_AVERAGE_SCORE_BONUS)
        self.assertEqual(state.score, BELOW_AVERAGE_SCORE_BONUS)

    def test_upgrade_adds_bonus_and_tracks_building(self):
        state = GameState(self.records)
        result = state.advance_turn(upgrade_building=Building.POWER_PLANT)
        self.assertEqual(result.upgraded_building, Building.POWER_PLANT)
        self.assertEqual(state.upgrades[Building.POWER_PLANT], 1)
        self.assertEqual(result.score_delta, BELOW_AVERAGE_SCORE_BONUS + UPGRADE_SCORE_BONUS)

    def test_above_average_month_penalized(self):
        state = GameState(self.records)
        state.advance_turn()  # Aug - below average
        result = state.advance_turn()  # Sep - also below average, skip to Oct instead
        # Advance to October (index 2), which is above the 12-month average.
        result = state.advance_turn()
        self.assertFalse(result.beat_average)
        self.assertEqual(result.score_delta, -ABOVE_AVERAGE_SCORE_PENALTY)

    def test_full_run_produces_rating(self):
        state = GameState(self.records)
        while not state.is_finished:
            state.advance_turn()
        self.assertEqual(len(state.history), 12)
        rating = state.final_rating()
        self.assertIsInstance(rating, Rating)
        # 6 of 12 real months fall at/below the dataset's own average.
        months_below = sum(1 for r in state.history if r.beat_average)
        self.assertEqual(months_below, 6)
        self.assertEqual(rating, Rating.BRONZE)

    def test_cannot_advance_past_end(self):
        state = GameState(self.records)
        for _ in range(12):
            state.advance_turn()
        with self.assertRaises(RuntimeError):
            state.advance_turn()


if __name__ == "__main__":
    unittest.main()
