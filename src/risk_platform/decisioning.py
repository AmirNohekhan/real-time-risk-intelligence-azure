from risk_platform.domain import Action, RiskCategory


def combine_scores(supervised: float, anomaly: float) -> float:
    """Weighted evidence policy: supervised signal dominates, anomaly adds novel-risk evidence."""
    return min(1.0, max(0.0, 0.75 * supervised + 0.25 * anomaly))


def decide(
    score: float, review_threshold: float, block_threshold: float
) -> tuple[RiskCategory, Action]:
    if not 0 <= review_threshold < block_threshold <= 1:
        raise ValueError("thresholds must satisfy 0 <= review < block <= 1")
    if score >= block_threshold:
        return RiskCategory.HIGH, Action.BLOCK
    if score >= review_threshold:
        return RiskCategory.MEDIUM, Action.REVIEW
    return RiskCategory.LOW, Action.APPROVE
