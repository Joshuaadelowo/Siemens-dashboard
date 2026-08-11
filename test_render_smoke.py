"""Headless render check: draws every turn to an offscreen surface via SDL's
dummy video driver, so this runs without a real display (e.g. in CI)."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from data_loader import compute_ranges, load_monthly_records
from scoring import Building, GameState


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

    def test_draws_all_twelve_turns_without_crashing(self):
        import game

        records = load_monthly_records()
        ranges = compute_ranges(records)
        state = GameState(records)
        surface = pygame.Surface(game.WINDOW_SIZE)

        selections = [None, Building.POWER_PLANT, Building.BOILER, Building.WATER_TOWER] * 3
        for selected in selections:
            game.draw_frame(surface, self.fonts, ranges, state, selected)
            assert_not_blank(surface)
            state.advance_turn(upgrade_building=selected)

        self.assertTrue(state.is_finished)

    def test_draws_end_screen_without_crashing(self):
        import game

        records = load_monthly_records()
        state = GameState(records)
        for _ in range(12):
            state.advance_turn()

        surface = pygame.Surface(game.WINDOW_SIZE)
        game.draw_frame(surface, self.fonts, {}, state, None)
        assert_not_blank(surface)


if __name__ == "__main__":
    unittest.main()
