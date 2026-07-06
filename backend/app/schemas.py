from typing import Any

from pydantic import BaseModel, Field


class DamageCounts(BaseModel):
    none: int = 0
    minor: int = 0
    major: int = 0
    destroyed: int = 0


class Zone(BaseModel):
    rank: int
    bbox: list[int] = Field(description="x, y, width, height in pixels")
    damage_counts: DamageCounts
    priority_score: float


class AnalysisSummary(BaseModel):
    total_building_pixels: int
    destroyed_pct: float
    major_pct: float
    minor_pct: float


class AnalysisResult(BaseModel):
    zones: list[Zone]
    summary: AnalysisSummary
    mask_path: str | None = None
    mask_base64: str | None = None
    pair_id: str | None = None
    inference_mode: str


class BriefRequest(BaseModel):
    analysis: dict[str, Any]
    context: str | None = None


class BriefResponse(BaseModel):
    brief: str
    source: str  # fireworks | stub


class DemoPair(BaseModel):
    id: str
    disaster_type: str
    pre_image: str
    post_image: str
