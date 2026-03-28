"""
MuHive Scoring System
─────────────────────
Mathematical logic to compute 'Trust Scores'.
Weights various factors like source reliability, LLM grounding, and consistency.

Functions:
- compute_trust_score: Aggregates multiple metrics into a 0-100 score
"""

def compute_trust_score(
    relevance_score: float,
    source_tier: float,
    detail_score: float,
    consistency_score: float,
    grounding_score: float,
    has_unsupported_claims: bool,
    cfg: dict,
) -> float:
    """
    Calculates a weighted average Trust Score.
    """
    w = cfg["stage2"]["trust_weights"]
    
    # Normalize relevance from 0-5 to 0-1
    r_norm = min(relevance_score / 5.0, 1.0)
    
    # Penalty for unsupported claims (P = 1.0 if penalty exists)
    penalty = 1.0 if has_unsupported_claims else 0.0

    raw_score = 100.0 * (
        w["relevance"] * r_norm +
        w["source_tier"] * source_tier +
        w["detail"] * detail_score +
        w["consistency"] * consistency_score +
        w["penalty_missing"] * (1.0 - penalty) +
        w["grounding"] * grounding_score +
        w["verification"] * grounding_score
    )
    
    return round(min(max(raw_score, 0.0), 100.0), 2)
