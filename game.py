"""Campus Builder — a small pygame front end for real Siemens facility data.

Turns real monthly electricity/gas/water readings (see data_loader.py) into a
12-turn campus-builder game: fill-meters on three buildings and a smog overlay
stand in for the raw numbers, so the game's framing does the "make this
approachable" work instead of chart polish.

Requires a display and `pip install pygame` (see requirements.txt). Only this
file imports pygame — data_loader.py and scoring.py stay headless-testable.
"""

import sys

import pygame

from data_loader import MonthlyRecord, compute_ranges, load_monthly_records
from scoring import Building, GameState, Rating

WINDOW_SIZE = (900, 620)
BG_COLOR = (235, 240, 235)
TEXT_COLOR = (30, 30, 30)
MUTED_TEXT_COLOR = (90, 90, 90)

BUILDING_LABELS = {
    Building.POWER_PLANT: "Power Plant",
    Building.BOILER: "Boiler",
    Building.WATER_TOWER: "Water Tower",
}
BUILDING_METRIC = {
    Building.POWER_PLANT: "electricity_kwh",
    Building.BOILER: "gas_kwh",
    Building.WATER_TOWER: "water_m3",
}
BUILDING_FILL_COLOR = {
    Building.POWER_PLANT: (240, 200, 40),
    Building.BOILER: (210, 90, 40),
    Building.WATER_TOWER: (60, 130, 200),
}
BUILDING_KEYS = {
    pygame.K_1: Building.POWER_PLANT,
    pygame.K_2: Building.BOILER,
    pygame.K_3: Building.WATER_TOWER,
}

BUILDING_WIDTH = 160
BUILDING_HEIGHT = 220
BUILDING_Y = 300
BUILDING_XS = {
    Building.POWER_PLANT: 90,
    Building.BOILER: 370,
    Building.WATER_TOWER: 650,
}

RATING_COLOR = {
    Rating.GOLD: (200, 160, 40),
    Rating.SILVER: (140, 140, 150),
    Rating.BRONZE: (150, 90, 50),
    Rating.NEEDS_IMPROVEMENT: (120, 60, 60),
}


def scale_fraction(value: float, value_range: tuple[float, float]) -> float:
    low, high = value_range
    if high <= low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))


def draw_text(surface, font, text, pos, color=TEXT_COLOR, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(rendered, rect)
    return rect


def draw_building(surface, font, building: Building, record: MonthlyRecord, ranges, upgraded_count: int, selected: bool):
    x = BUILDING_XS[building]
    metric_name = BUILDING_METRIC[building]
    value = getattr(record, metric_name)
    fraction = scale_fraction(value, ranges[metric_name])

    outline_color = (20, 120, 60) if selected else (60, 60, 60)
    pygame.draw.rect(surface, (255, 255, 255), (x, BUILDING_Y, BUILDING_WIDTH, BUILDING_HEIGHT))
    pygame.draw.rect(surface, outline_color, (x, BUILDING_Y, BUILDING_WIDTH, BUILDING_HEIGHT), width=3 if selected else 2)

    fill_height = int(BUILDING_HEIGHT * fraction)
    fill_rect = (x, BUILDING_Y + BUILDING_HEIGHT - fill_height, BUILDING_WIDTH, fill_height)
    pygame.draw.rect(surface, BUILDING_FILL_COLOR[building], fill_rect)

    if building is Building.BOILER:
        puff_count = 1 + int(fraction * 4)
        for i in range(puff_count):
            puff_x = x + BUILDING_WIDTH // 2 + (i - puff_count // 2) * 14
            puff_y = BUILDING_Y - 12 - i * 10
            radius = 6 + int(fraction * 6)
            pygame.draw.circle(surface, (170, 170, 170), (puff_x, puff_y), radius)

    label = BUILDING_LABELS[building]
    draw_text(surface, font, label, (x + BUILDING_WIDTH // 2, BUILDING_Y - 26), center=True)
    draw_text(surface, font, f"{value:,.0f}", (x + BUILDING_WIDTH // 2, BUILDING_Y + BUILDING_HEIGHT + 18), center=True)

    if upgraded_count:
        badge_center = (x + BUILDING_WIDTH - 14, BUILDING_Y + 14)
        pygame.draw.circle(surface, (40, 160, 90), badge_center, 12)
        draw_text(surface, font, str(upgraded_count), badge_center, color=(255, 255, 255), center=True)


def draw_carbon_overlay(surface, record: MonthlyRecord, ranges):
    fraction = scale_fraction(record.carbon_tonnes, ranges["carbon_tonnes"])
    overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
    overlay.fill((120, 120, 110, int(140 * fraction)))
    surface.blit(overlay, (0, 0))


def draw_hud(surface, fonts, record: MonthlyRecord, state: GameState):
    small, medium, large = fonts
    draw_text(surface, large, f"{record.month_label}", (30, 20))
    draw_text(surface, medium, f"Turn {state.turn_index + 1} / {len(state.records)}", (30, 60))
    draw_text(surface, medium, f"Score: {state.score}", (30, 90))

    beats_average = record.carbon_tonnes <= state.average
    verdict = "below average" if beats_average else "above average"
    verdict_color = (30, 120, 60) if beats_average else (150, 60, 40)
    draw_text(
        surface, medium,
        f"Carbon this month: {record.carbon_tonnes:.1f}t ({verdict}, avg {state.average:.1f}t)",
        (30, 120), color=verdict_color,
    )
    draw_text(surface, medium, f"~{record.homes_equivalent:,.0f} UK 2-bed homes powered this month", (30, 150))

    draw_text(
        surface, small,
        "Press 1/2/3 to spend your Efficiency Token on a building, SPACE for next month",
        (30, WINDOW_SIZE[1] - 40), color=MUTED_TEXT_COLOR,
    )


def draw_end_screen(surface, fonts, state: GameState):
    small, medium, large = fonts
    rating = state.final_rating()
    months_below = sum(1 for r in state.history if r.beat_average)

    surface.fill(BG_COLOR)
    draw_text(surface, large, "12 Months Complete", (WINDOW_SIZE[0] // 2, 160), center=True)
    draw_text(
        surface, large, rating.value, (WINDOW_SIZE[0] // 2, 230),
        color=RATING_COLOR[rating], center=True,
    )
    draw_text(surface, medium, f"Final score: {state.score}", (WINDOW_SIZE[0] // 2, 300), center=True)
    draw_text(
        surface, medium, f"{months_below} of 12 months at or below the campus's own average",
        (WINDOW_SIZE[0] // 2, 330), center=True,
    )
    draw_text(surface, small, "Press ESC to quit", (WINDOW_SIZE[0] // 2, 400), color=MUTED_TEXT_COLOR, center=True)


def draw_frame(surface, fonts, ranges, state: GameState, selected_building):
    surface.fill(BG_COLOR)
    if state.is_finished:
        draw_end_screen(surface, fonts, state)
        return

    record = state.current_record
    draw_hud(surface, fonts, record, state)
    for building in Building:
        draw_building(
            surface, fonts[0], building, record, ranges,
            upgraded_count=state.upgrades[building],
            selected=(building is selected_building),
        )
    draw_carbon_overlay(surface, record, ranges)


def build_game(data_path=None):
    records = load_monthly_records(data_path) if data_path else load_monthly_records()
    ranges = compute_ranges(records)
    state = GameState(records)
    return state, ranges


def main():
    pygame.init()
    pygame.display.set_caption("Campus Builder")
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()
    fonts = (
        pygame.font.SysFont(None, 20),
        pygame.font.SysFont(None, 26),
        pygame.font.SysFont(None, 40),
    )

    state, ranges = build_game()
    selected_building = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif not state.is_finished and event.key in BUILDING_KEYS:
                    candidate = BUILDING_KEYS[event.key]
                    selected_building = None if selected_building is candidate else candidate
                elif not state.is_finished and event.key == pygame.K_SPACE:
                    state.advance_turn(upgrade_building=selected_building)
                    selected_building = None

        draw_frame(screen, fonts, ranges, state, selected_building)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
