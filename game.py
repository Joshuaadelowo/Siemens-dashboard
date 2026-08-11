"""Campus Carbon Forecaster — a small pygame front end for real Siemens facility data.

"The Price is Right" for utility data: each round shows the previous month's
real carbon footprint and asks the player to slide a marker to where they
think the next month landed (see data_loader.py for the underlying readings).
Score is based on how close the guess is to the real number.

Requires a display and `pip install pygame` (see requirements.txt). Only this
file imports pygame — data_loader.py and scoring.py stay headless-testable.
"""

import sys

import pygame

from data_loader import compute_ranges, load_monthly_records
from scoring import GUESS_ROUNDS, GameState, Rating, TurnResult

WINDOW_SIZE = (900, 500)
BG_COLOR = (235, 240, 235)
TEXT_COLOR = (30, 30, 30)
MUTED_TEXT_COLOR = (90, 90, 90)

LINE_X0 = 90
LINE_X1 = 810
LINE_Y = 300
RANGE_PADDING_FRACTION = 0.15
GUESS_SPEED_FRACTION = 0.5  # fraction of the slider span crossed per second, holding an arrow key

REFERENCE_COLOR = (140, 140, 150)
GUESS_COLOR = (60, 130, 200)
ACTUAL_COLOR = (40, 160, 90)
MISS_COLOR = (190, 90, 60)

RATING_COLOR = {
    Rating.GOLD: (200, 160, 40),
    Rating.SILVER: (140, 140, 150),
    Rating.BRONZE: (150, 90, 50),
    Rating.NEEDS_IMPROVEMENT: (120, 60, 60),
}


def padded_carbon_range(records) -> tuple[float, float]:
    low, high = compute_ranges(records)["carbon_tonnes"]
    pad = (high - low) * RANGE_PADDING_FRACTION or 1.0
    return low - pad, high + pad


def value_to_x(value: float, value_range: tuple[float, float]) -> float:
    low, high = value_range
    fraction = 0.5 if high <= low else (value - low) / (high - low)
    fraction = max(0.0, min(1.0, fraction))
    return LINE_X0 + fraction * (LINE_X1 - LINE_X0)


def draw_text(surface, font, text, pos, color=TEXT_COLOR, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(rendered, rect)
    return rect


def draw_marker(surface, font, x, label, color, y=LINE_Y, label_above=True):
    pygame.draw.circle(surface, color, (int(x), y), 9)
    pygame.draw.circle(surface, (255, 255, 255), (int(x), y), 9, width=2)
    label_y = y - 26 if label_above else y + 22
    draw_text(surface, font, label, (x, label_y), color=color, center=True)


def draw_number_line(surface, fonts, slider_range, reference_value, guess_value, result: TurnResult | None):
    small, medium, _ = fonts
    pygame.draw.line(surface, (170, 170, 170), (LINE_X0, LINE_Y), (LINE_X1, LINE_Y), 4)

    low, high = slider_range
    draw_text(surface, small, f"{low:.0f}t", (LINE_X0, LINE_Y + 34), color=MUTED_TEXT_COLOR, center=True)
    draw_text(surface, small, f"{high:.0f}t", (LINE_X1, LINE_Y + 34), color=MUTED_TEXT_COLOR, center=True)

    draw_marker(surface, small, value_to_x(reference_value, slider_range), "prev month", REFERENCE_COLOR)

    if result is None:
        draw_marker(surface, small, value_to_x(guess_value, slider_range), f"your guess: {guess_value:.1f}t", GUESS_COLOR, label_above=False)
    else:
        guess_x = value_to_x(result.guess, slider_range)
        actual_x = value_to_x(result.actual, slider_range)
        draw_marker(surface, small, guess_x, f"guess: {result.guess:.1f}t", GUESS_COLOR, label_above=False)
        draw_marker(surface, small, actual_x, f"actual: {result.actual:.1f}t", ACTUAL_COLOR)


def draw_hud(surface, fonts, state: GameState, result: TurnResult | None):
    small, medium, large = fonts
    reference = result.reference_record if result is not None else state.reference_record
    target = result.target_record if result is not None else state.target_record
    displayed_round = state.turn_index if result is not None else state.turn_index + 1

    draw_text(surface, large, f"Round {displayed_round} / {GUESS_ROUNDS}", (30, 20))
    draw_text(surface, medium, f"Score: {state.score}", (30, 60))
    draw_text(
        surface, medium,
        f"{reference.month_label}: {reference.carbon_tonnes:.1f}t CO2e actual",
        (30, 100), color=MUTED_TEXT_COLOR,
    )

    if result is None:
        draw_text(surface, medium, f"Guess {target.month_label}'s carbon footprint", (30, 130))
        draw_text(
            surface, small,
            "LEFT/RIGHT to move your guess, SPACE to lock it in",
            (30, WINDOW_SIZE[1] - 40), color=MUTED_TEXT_COLOR,
        )
    else:
        verdict_color = ACTUAL_COLOR if result.score_delta >= 70 else (MISS_COLOR if result.score_delta < 40 else TEXT_COLOR)
        draw_text(
            surface, medium,
            f"Off by {result.error:.1f}t — +{result.score_delta} points",
            (30, 130), color=verdict_color,
        )
        draw_text(
            surface, small,
            "SPACE to continue",
            (30, WINDOW_SIZE[1] - 40), color=MUTED_TEXT_COLOR,
        )


def draw_end_screen(surface, fonts, state: GameState):
    small, medium, large = fonts
    rating = state.final_rating()
    average_error = sum(r.error for r in state.history) / len(state.history)

    surface.fill(BG_COLOR)
    draw_text(surface, large, "12 Months Complete", (WINDOW_SIZE[0] // 2, 140), center=True)
    draw_text(
        surface, large, rating.value, (WINDOW_SIZE[0] // 2, 200),
        color=RATING_COLOR[rating], center=True,
    )
    draw_text(surface, medium, f"Final score: {state.score} / {len(state.history) * 100}", (WINDOW_SIZE[0] // 2, 270), center=True)
    draw_text(
        surface, medium, f"Average miss: {average_error:.1f}t CO2e",
        (WINDOW_SIZE[0] // 2, 300), center=True,
    )
    draw_text(surface, small, "Press ESC to quit", (WINDOW_SIZE[0] // 2, 380), color=MUTED_TEXT_COLOR, center=True)


def draw_frame(surface, fonts, state: GameState, slider_range, guess_value: float, result: TurnResult | None):
    surface.fill(BG_COLOR)
    if state.is_finished:
        draw_end_screen(surface, fonts, state)
        return

    draw_hud(surface, fonts, state, result)
    reference_value = result.reference_record.carbon_tonnes if result is not None else state.reference_record.carbon_tonnes
    draw_number_line(surface, fonts, slider_range, reference_value, guess_value, result)


def build_game(data_path=None):
    records = load_monthly_records(data_path) if data_path else load_monthly_records()
    state = GameState(records)
    slider_range = padded_carbon_range(records)
    return state, slider_range


def main():
    pygame.init()
    pygame.display.set_caption("Campus Carbon Forecaster")
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()
    fonts = (
        pygame.font.SysFont(None, 20),
        pygame.font.SysFont(None, 26),
        pygame.font.SysFont(None, 40),
    )

    state, slider_range = build_game()
    slider_low, slider_high = slider_range
    slider_span = slider_high - slider_low
    guess_value = state.reference_record.carbon_tonnes
    result = None

    running = True
    while running:
        dt = clock.tick(30) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and not state.is_finished:
                    if result is None:
                        result = state.advance_turn(guess_value)
                    else:
                        result = None
                        if not state.is_finished:
                            guess_value = state.reference_record.carbon_tonnes

        if result is None and not state.is_finished:
            keys = pygame.key.get_pressed()
            speed = slider_span * GUESS_SPEED_FRACTION
            if keys[pygame.K_LEFT]:
                guess_value -= speed * dt
            if keys[pygame.K_RIGHT]:
                guess_value += speed * dt
            guess_value = max(slider_low, min(slider_high, guess_value))

        draw_frame(screen, fonts, state, slider_range, guess_value, result)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
