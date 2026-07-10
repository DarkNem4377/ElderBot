from __future__ import annotations

import json

import httpx
import pytest

from app.services import narrator

_ANALYSIS = {
    "summary": {"total_buildings": 4, "destroyed_pct": 25.0, "major_pct": 25.0, "minor_pct": 50.0},
    "zones": [
        {
            "rank": 1,
            "priority_score": 87.5,
            "building_counts": {"none": 0, "minor": 1, "major": 1, "destroyed": 2},
        }
    ],
    "mask_base64": "A" * 50_000,
    "mask_path": "/srv/outputs/deadbeef/damage_mask.png",
}


@pytest.fixture
def captured_payload(monkeypatch):
    """Intercept the Fireworks request and hand back its JSON body."""
    monkeypatch.setattr(narrator.settings, "fireworks_api_key", "test-key")
    captured: dict = {}

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json, headers):
            captured.update(json)
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Deploy to zone 1."}}]},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(narrator.httpx, "AsyncClient", lambda **kw: _FakeClient())
    return captured


@pytest.mark.anyio
async def test_mask_base64_never_reaches_the_llm(captured_payload):
    result = await narrator.generate_brief(dict(_ANALYSIS))

    assert result.source == "fireworks"
    prompt = captured_payload["messages"][1]["content"]
    assert "mask_base64" not in prompt
    assert "mask_path" not in prompt
    assert "AAAA" not in prompt
    # The zone data the brief is supposed to narrate must survive the filter.
    assert "priority_score" in prompt


@pytest.mark.anyio
async def test_generate_brief_does_not_mutate_callers_analysis(captured_payload):
    analysis = dict(_ANALYSIS)
    await narrator.generate_brief(analysis)
    assert "mask_base64" in analysis


@pytest.mark.anyio
async def test_context_is_truncated(captured_payload):
    await narrator.generate_brief(dict(_ANALYSIS), context="x" * 5000)

    sent = json.loads(captured_payload["messages"][1]["content"])
    assert len(sent["context"]) == narrator.MAX_CONTEXT_CHARS


@pytest.mark.anyio
async def test_network_failure_falls_back_to_stub(monkeypatch):
    monkeypatch.setattr(narrator.settings, "fireworks_api_key", "test-key")

    class _FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, *a, **kw):
            raise httpx.ConnectError("fireworks unreachable")

    monkeypatch.setattr(narrator.httpx, "AsyncClient", lambda **kw: _FailingClient())

    result = await narrator.generate_brief(dict(_ANALYSIS))

    assert result.source == "fireworks-fallback"
    assert "Zone #1" in result.brief


@pytest.mark.anyio
async def test_empty_completion_falls_back_to_stub(monkeypatch):
    """Reasoning models can burn the whole token budget and return null content."""
    monkeypatch.setattr(narrator.settings, "fireworks_api_key", "test-key")

    class _EmptyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json, headers):
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": None}}]},
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr(narrator.httpx, "AsyncClient", lambda **kw: _EmptyClient())

    result = await narrator.generate_brief(dict(_ANALYSIS))
    assert result.source == "fireworks-fallback"


@pytest.mark.anyio
async def test_missing_api_key_serves_stub(monkeypatch):
    monkeypatch.setattr(narrator.settings, "fireworks_api_key", "")
    result = await narrator.generate_brief(dict(_ANALYSIS))
    assert result.source == "stub"
