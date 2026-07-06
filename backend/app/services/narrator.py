"""Fireworks LLM narrator — narrates ranked JSON only, never re-ranks."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import settings
from app.schemas import BriefResponse

SYSTEM_PROMPT = """You are a disaster response analyst. You receive a JSON object with
deterministic damage zone scores from satellite imagery analysis.

Rules:
- Narrate the situation in plain language for emergency coordinators.
- Reference zone ranks and damage counts exactly as provided.
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
        f"Overall: {summary.get('total_building_pixels', 0)} building pixels assessed. "
        f"Destroyed: {summary.get('destroyed_pct', 0)}%, "
        f"Major: {summary.get('major_pct', 0)}%, "
        f"Minor: {summary.get('minor_pct', 0)}%."
    )
    lines.append("")
    lines.append("Priority zones (pre-ranked by ML):")
    for z in zones:
        dc = z.get("damage_counts", {})
        lines.append(
            f"  Zone #{z.get('rank')}: score {z.get('priority_score')} — "
            f"destroyed={dc.get('destroyed', 0)}, major={dc.get('major', 0)}, "
            f"minor={dc.get('minor', 0)}, undamaged={dc.get('none', 0)}"
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
        "max_tokens": 512,
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
        content = data["choices"][0]["message"]["content"]
        return BriefResponse(brief=content.strip(), source="fireworks")
