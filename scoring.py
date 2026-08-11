from dataclasses import dataclass
from enum import Enum

from data_loader import MonthlyRecord

TOKENS_PER_GAME = 12
UPGRADE_SCORE_BONUS = 10
BELOW_AVERAGE_SCORE_BONUS = 15
ABOVE_AVERAGE_SCORE_PENALTY = 5

Building = Enum("Building", ["POWER_PLANT", "BOILER", "WATER_TOWER"])


@dataclass
class TurnResult:
    record: MonthlyRecord
    average_carbon_tonnes: float
    beat_average: bool
    upgraded_building: Building | None
    score_delta: int
    running_score: int


class Rating(Enum):
    NEEDS_IMPROVEMENT = "Needs Improvement"
    BRONZE = "Bronze Campus"
    SILVER = "Silver Campus"
    GOLD = "Gold Campus"


def average_carbon_tonnes(records: list[MonthlyRecord]) -> float:
    return sum(r.carbon_tonnes for r in records) / len(records)


class GameState:
    """Pure, headless-testable turn/score tracker for a 12-month run."""

    def __init__(self, records: list[MonthlyRecord]):
        if len(records) != TOKENS_PER_GAME:
            raise ValueError(f"Expected {TOKENS_PER_GAME} monthly records, got {len(records)}")
        self.records = records
        self.average = average_carbon_tonnes(records)
        self.turn_index = 0
        self.score = 0
        self.upgrades: dict[Building, int] = {b: 0 for b in Building}
        self.history: list[TurnResult] = []

    @property
    def is_finished(self) -> bool:
        return self.turn_index >= len(self.records)

    @property
    def current_record(self) -> MonthlyRecord:
        return self.records[self.turn_index]

    def advance_turn(self, upgrade_building: Building | None = None) -> TurnResult:
        if self.is_finished:
            raise RuntimeError("Game already finished; no more turns to advance.")

        record = self.current_record
        beat_average = record.carbon_tonnes <= self.average

        delta = BELOW_AVERAGE_SCORE_BONUS if beat_average else -ABOVE_AVERAGE_SCORE_PENALTY
        if upgrade_building is not None:
            self.upgrades[upgrade_building] += 1
            delta += UPGRADE_SCORE_BONUS

        self.score += delta
        self.turn_index += 1

        result = TurnResult(
            record=record,
            average_carbon_tonnes=self.average,
            beat_average=beat_average,
            upgraded_building=upgrade_building,
            score_delta=delta,
            running_score=self.score,
        )
        self.history.append(result)
        return result

    def final_rating(self) -> Rating:
        if not self.is_finished:
            raise RuntimeError("Game not finished yet.")
        months_below_average = sum(1 for r in self.history if r.beat_average)
        if months_below_average >= 9:
            return Rating.GOLD
        if months_below_average >= 7:
            return Rating.SILVER
        if months_below_average >= 5:
            return Rating.BRONZE
        return Rating.NEEDS_IMPROVEMENT
