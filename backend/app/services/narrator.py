"""Fireworks LLM narrator — narrates ranked JSON only, never re-ranks."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings
from app.schemas import BriefResponse

SYSTEM_PROMPT = """You are a disaster response analyst. You receive a JSON object with
deterministic per-zone building damage counts and priority scores from satellite
imagery analysis.

Rules:
- Narrate the situation in plain language for emergency coordinators.
- Reference zone ranks and building counts exactly as provided.
- Do NOT change rankings, scores, or invent additional damage data.
- Keep the brief under 250 words.
- Mention priority zones first and recommend where to deploy resources first.
"""


def _stub_brief(analysis: dict[str, Any], context: str | None) -> str:
    summary = analysis.get("summary", {})
    zones = analysis.get("zones", [])[:3]
    lines = [
        "SITUATION BRIEF (stub — set FIREWORKS_API_KEY for live narration)",
        "",
    ]
    if context:
        lines.append(f"Context: {context}")
        lines.append("")
    lines.append(
        f"Overall: {summary.get('total_buildings', 0)} buildings assessed. "
        f"Destroyed: {summary.get('destroyed_pct', 0)}%, "
        f"Major: {summary.get('major_pct', 0)}%, "
        f"Minor: {summary.get('minor_pct', 0)}%."
    )
    lines.append("")
    lines.append("Priority zones (pre-ranked by ML):")
    for z in zones:
        bc = z.get("building_counts", {})
        lines.append(
            f"  Zone #{z.get('rank')}: score {z.get('priority_score')} — "
            f"destroyed={bc.get('destroyed', 0)}, major={bc.get('major', 0)}, "
            f"minor={bc.get('minor', 0)}, undamaged={bc.get('none', 0)} buildings"
        )
    lines.append("")
    lines.append(
        "Recommendation: Deploy assessment teams to highest-scored zones first "
        "while verifying access routes and secondary hazards."
    )
    return "\n".join(lines)


async def generate_brief(analysis: dict[str, Any], context: str | None = None) -> BriefResponse:
    if not settings.fireworks_api_key:
        return BriefResponse(brief=_stub_brief(analysis, context), source="stub")

    user_content = json.dumps({"analysis": analysis, "context": context}, indent=2)
    payload = {
        "model": settings.fireworks_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        # gpt-oss-120b is a reasoning model: reasoning tokens share this budget,
        # so keep enough headroom that the <250-word brief is never truncated.
        "max_tokens": 1500,
        "temperature": 0.3,
    }
    headers = {
        "Authorization": f"Bearer {settings.fireworks_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.fireworks.ai/inference/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        message = data["choices"][0]["message"]
        # Reasoning models can leave `content` null if they spend the whole
        # budget reasoning; fall back to the stub rather than crashing.
        content = (message.get("content") or "").strip()
        if not content:
            return BriefResponse(brief=_stub_brief(analysis, context), source="stub")
        return BriefResponse(brief=content, source="fireworks")
