import unittest

from data_loader import load_monthly_records
from scoring import (
    GUESS_ROUNDS,
    MAX_TURN_SCORE,
    GameState,
    Rating,
    carbon_span,
)


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.records = load_monthly_records()

    def test_span_matches_expected(self):
        # 97.67t (Oct) - 55.55t (Jul) from the real dataset.
        self.assertAlmostEqual(carbon_span(self.records), 42.12, places=1)

    def test_rejects_wrong_record_count(self):
        with self.assertRaises(ValueError):
            GameState(self.records[:5])

    def test_perfect_guess_scores_max(self):
        state = GameState(self.records)
        actual = state.target_record.carbon_tonnes
        result = state.advance_turn(actual)
        self.assertEqual(result.error, 0)
        self.assertEqual(result.score_delta, MAX_TURN_SCORE)
        self.assertEqual(state.score, MAX_TURN_SCORE)

    def test_wildly_wrong_guess_scores_near_zero(self):
        state = GameState(self.records)
        actual = state.target_record.carbon_tonnes
        result = state.advance_turn(actual + 1000)
        self.assertEqual(result.score_delta, 0)

    def test_advance_turn_moves_reference_and_target(self):
        state = GameState(self.records)
        first_reference = state.reference_record
        first_target = state.target_record
        state.advance_turn(first_target.carbon_tonnes)
        self.assertIs(state.reference_record, first_target)
        self.assertIsNot(state.reference_record, first_reference)

    def test_full_run_produces_rating(self):
        state = GameState(self.records)
        while not state.is_finished:
            # Always guess the reference month's own value, i.e. "no change".
            state.advance_turn(state.reference_record.carbon_tonnes)
        self.assertEqual(len(state.history), GUESS_ROUNDS)
        rating = state.final_rating()
        self.assertIsInstance(rating, Rating)

    def test_cannot_advance_past_end(self):
        state = GameState(self.records)
        for _ in range(GUESS_ROUNDS):
            state.advance_turn(state.reference_record.carbon_tonnes)
        with self.assertRaises(RuntimeError):
            state.advance_turn(0)


if __name__ == "__main__":
    unittest.main()
