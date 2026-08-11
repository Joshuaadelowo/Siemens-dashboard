from dataclasses import dataclass
from enum import Enum

from data_loader import MonthlyRecord

MONTHS_PER_GAME = 12
GUESS_ROUNDS = MONTHS_PER_GAME - 1
MAX_TURN_SCORE = 100


@dataclass
class TurnResult:
    reference_record: MonthlyRecord
    target_record: MonthlyRecord
    guess: float
    actual: float
    error: float
    score_delta: int
    running_score: int


class Rating(Enum):
    NEEDS_IMPROVEMENT = "Needs Improvement"
    BRONZE = "Bronze Forecaster"
    SILVER = "Silver Forecaster"
    GOLD = "Gold Forecaster"


def carbon_span(records: list[MonthlyRecord]) -> float:
    values = [r.carbon_tonnes for r in records]
    return max(values) - min(values)


class GameState:
    """Pure, headless-testable turn/score tracker for an 11-round carbon-guessing game.

    Each round shows the player one month's carbon footprint (the "reference")
    and asks them to guess the next month's ("target"). Score per round is
    scaled by how close the guess lands relative to the dataset's own carbon
    range, so a wildly wrong guess on a low-variance dataset still costs you.
    """

    def __init__(self, records: list[MonthlyRecord]):
        if len(records) != MONTHS_PER_GAME:
            raise ValueError(f"Expected {MONTHS_PER_GAME} monthly records, got {len(records)}")
        self.records = records
        self.span = carbon_span(records)
        self.turn_index = 0
        self.score = 0
        self.history: list[TurnResult] = []

    @property
    def is_finished(self) -> bool:
        return self.turn_index >= GUESS_ROUNDS

    @property
    def reference_record(self) -> MonthlyRecord:
        return self.records[self.turn_index]

    @property
    def target_record(self) -> MonthlyRecord:
        return self.records[self.turn_index + 1]

    def advance_turn(self, guess: float) -> TurnResult:
        if self.is_finished:
            raise RuntimeError("Game already finished; no more turns to advance.")

        reference = self.reference_record
        target = self.target_record
        actual = target.carbon_tonnes
        error = abs(guess - actual)
        score_delta = round(max(0.0, MAX_TURN_SCORE * (1 - error / self.span))) if self.span else MAX_TURN_SCORE

        self.score += score_delta
        self.turn_index += 1

        result = TurnResult(
            reference_record=reference,
            target_record=target,
            guess=guess,
            actual=actual,
            error=error,
            score_delta=score_delta,
            running_score=self.score,
        )
        self.history.append(result)
        return result

    def final_rating(self) -> Rating:
        if not self.is_finished:
            raise RuntimeError("Game not finished yet.")
        average_score = self.score / len(self.history)
        if average_score >= 80:
            return Rating.GOLD
        if average_score >= 60:
            return Rating.SILVER
        if average_score >= 40:
            return Rating.BRONZE
        return Rating.NEEDS_IMPROVEMENT
