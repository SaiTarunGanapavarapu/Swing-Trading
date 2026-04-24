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


def scoreTieredZScore(zscore, tiers, inverse=False):
    """Score based on z-score instead of raw values.
    
    tiers format: [(zscore_threshold, points, grade), ...]
    For example: [(-1.0, 5, "excellent"), (0.0, 3, "good"), (1.0, 1, "fair")]
    
    inverse=True: lower z-scores are better (e.g., for PE ratio)
    inverse=False: higher z-scores are better (e.g., for growth)
    """
    if zscore is None or (isinstance(zscore, float) and math.isnan(zscore)):
        return 0, "N/A"
    
    if inverse:
        # Lower z-scores are better, so check from lowest to highest
        for threshold, points, grade in sorted(tiers, key=lambda x: x[0]):
            if zscore <= threshold:
                return points, grade
        return 0, "poor"
    else:
        # Higher z-scores are better, so check from highest to lowest
        for threshold, points, grade in sorted(tiers, key=lambda x: x[0], reverse=True):
            if zscore >= threshold:
                return points, grade
        return 0, "poor"
