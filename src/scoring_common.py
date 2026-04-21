import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class RuleResult:
    ruleId: str
    ruleName: str
    source: str
    value: Optional[float]
    score: float
    maxScore: float
    grade: str


def scoreTiered(value, tiers, inverse=False):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0, "N/A"

    if inverse:
        for threshold, points, grade in tiers:
            if value <= threshold:
                return points, grade
        return 0, "poor"

    for threshold, points, grade in tiers:
        if value >= threshold:
            return points, grade
    return 0, "poor"
