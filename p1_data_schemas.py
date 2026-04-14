"""
MuHive Data Schemas

ScoutItem (input) → Stage2Result (output).
Internals: FastFilterResult, QualityResult (LLM structured outputs).
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional

# ==============================================================================
# SECTION 1: EXTERNAL SCHEMAS (Main API)
# ==============================================================================


class ScoutItem(BaseModel):
    """Input from Stage 1 Scout adapter."""
    title: str
    description: str
    url: str
    source: str
    deadline: Optional[str] = None


class GroupSlice(BaseModel):
    """Per-group classification + tailored output."""
    group: Literal["AI", "Cybersecurity", "WebDev"]
    relevance_score: float = Field(ge=0.0, le=5.0, description="0.0–5.0 from fast filter")
    match_reason: str = Field(description="One specific sentence explaining the match")
    tailored_summary: str = Field(default="", description="2-line summary tailored for this group")
    final_trust_score: float = Field(default=0.0, ge=0.0, le=100.0, description="0–100 after verifier")
    grounding_score: float = Field(default=0.0, ge=0.0, le=1.0, description="0.0–1.0 from search + verifier")
    ready_for_stage3: bool = Field(default=False, description="True if final_trust_score >= threshold")


class Stage2Result(BaseModel):
    """Complete Stage 2 output — storage-ready for Stage 3."""
    item_hash: str
    status: Literal["pass", "fail", "review"]
    group_slices: list[GroupSlice] = Field(default_factory=list)
    rough_score: float = Field(default=0.0, ge=0.0, le=5.0, description="Overall fast-filter score")
    fail_reason: Optional[str] = None
    review_needed: bool = False
    source_tier: float = Field(default=0.5, ge=0.0, le=1.0)
    search_used: bool = False
    search_snippet: Optional[str] = None
    verifier_notes: Optional[str] = None


# ==============================================================================
# SECTION 2: INTERNAL SCHEMAS (LLM Internals)
# ==============================================================================

class FastFilterGroupSlice(BaseModel):
    """Simplified group slice returned by the fast Groq classifier."""
    group: Literal["AI", "Cybersecurity", "WebDev"]
    relevance_score: float = Field(ge=0.0, le=5.0)
    match_reason: str


class FastFilterResult(BaseModel):
    """Groq fast-filter structured output."""
    rough_score: float = Field(ge=0.0, le=5.0)
    group_slices: list[FastFilterGroupSlice] = Field(default_factory=list)
    status: Literal["pass", "fail", "review"]
    fail_reason: Optional[str] = None


# ── Gemini / Quality Pass Schemas ──

class QualityGroupSlice(BaseModel):
    """Gemini quality pass — per-group tailored output."""
    group: Literal["AI", "Cybersecurity", "WebDev"]
    tailored_summary: str = Field(description="2-line tailored summary for this group")
    detail_score: float = Field(ge=0.0, le=1.0, description="How detailed the source content is")
    consistency_score: float = Field(ge=0.0, le=1.0, description="Internal consistency of claims")
    grounding_score: float = Field(ge=0.0, le=1.0, description="How well claims are grounded")
    unsupported_claims: list[str] = Field(default_factory=list, description="Flagged unsupported claims")


class QualityResult(BaseModel):
    """Gemini quality + verifier structured output."""
    group_slices: list[QualityGroupSlice] = Field(default_factory=list)
    verifier_notes: str = Field(default="", description="Summary of hallucination check")
