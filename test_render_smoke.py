"""Headless render check: draws every round to an offscreen surface via SDL's
dummy video driver, so this runs without a real display (e.g. in CI)."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_loader import load_monthly_records
from scoring import GUESS_ROUNDS, GameState


def assert_not_blank(surface):
    """Numpy-free stand-in for surfarray: sample a grid of pixels and check
    they aren't all identical, i.e. something was actually drawn."""
    width, height = surface.get_size()
    colors = {
        tuple(surface.get_at((x, y)))
        for x in range(0, width, 20)
        for y in range(0, height, 20)
    }
    if len(colors) <= 1:
        raise AssertionError("frame appears blank (all sampled pixels are the same color)")


class TestRenderSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))  # dummy driver still needs a display surface
        cls.fonts = (
            pygame.font.SysFont(None, 20),
            pygame.font.SysFont(None, 26),
            pygame.font.SysFont(None, 40),
        )

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_draws_all_rounds_without_crashing(self):
        import game

        records = load_monthly_records()
        state = GameState(records)
        slider_range = game.padded_carbon_range(records)
        surface = pygame.Surface(game.WINDOW_SIZE)

        for _ in range(GUESS_ROUNDS):
            guess_value = state.reference_record.carbon_tonnes
            game.draw_frame(surface, self.fonts, state, slider_range, guess_value, None)
            assert_not_blank(surface)

            result = state.advance_turn(guess_value)
            game.draw_frame(surface, self.fonts, state, slider_range, guess_value, result)
            assert_not_blank(surface)

        self.assertTrue(state.is_finished)

    def test_draws_end_screen_without_crashing(self):
        import game

        records = load_monthly_records()
        state = GameState(records)
        for _ in range(GUESS_ROUNDS):
            state.advance_turn(state.reference_record.carbon_tonnes)

        surface = pygame.Surface(game.WINDOW_SIZE)
        slider_range = game.padded_carbon_range(records)
        game.draw_frame(surface, self.fonts, state, slider_range, 0.0, None)
        assert_not_blank(surface)


if __name__ == "__main__":
    unittest.main()
