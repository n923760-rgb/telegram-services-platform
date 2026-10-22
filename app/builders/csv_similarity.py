"""Bounded lexical candidates for review, never entity or duplicate decisions."""

from dataclasses import dataclass

from rapidfuzz.fuzz import ratio

MAX_ROWS = 200
MAX_PAIRS = 1000
MIN_SCORE = 90.0


@dataclass(frozen=True)
class Pair:
    first: int
    second: int
    score: float
    columns: tuple[int, ...]


@dataclass(frozen=True)
class Review:
    pairs: tuple[Pair, ...]
    total: int


def review(rows: list[list[str]]) -> Review:
    if not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError("similarity row limit")
    width = len(rows[0])
    if not 1 <= width <= 20 or any(
        len(row) != width or any(not isinstance(value, str) or len(value) > 500 for value in row)
        for row in rows
    ):
        raise ValueError("invalid similarity rows")
    pairs = []
    total = 0
    # Compare cells, not concatenated records. Unchanged common columns cannot inflate a score.
    for second, current in enumerate(rows, 1):
        for first, earlier in enumerate(rows[: second - 1], 1):
            changed = tuple(
                i for i, (a, b) in enumerate(zip(earlier, current, strict=True), 1) if a != b
            )
            if not changed:
                continue  # Exact duplicates already have their own authoritative equality audit.
            score = 100.0
            for column in changed:
                a, b = earlier[column - 1], current[column - 1]
                # Different numeric-bearing values/empty cells are not lexical candidates.
                if not a.strip() or not b.strip() or any(char.isdigit() for char in a + b):
                    break
                value = ratio(a, b, processor=None, score_cutoff=MIN_SCORE)
                if value < MIN_SCORE:
                    break
                score = min(score, value)
            else:
                total += 1
                if len(pairs) < MAX_PAIRS:
                    pairs.append(Pair(first, second, round(score, 2), changed))
    return Review(tuple(pairs), total)
