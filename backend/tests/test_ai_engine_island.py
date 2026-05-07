import asyncio

import httpx
from openai import APIConnectionError
from app.constants.islands import DEFAULT_ISLAND_KEY, ISLAND_KEYS
from app.utils import ai_engine


def test_ai_prompts_loaded_from_json():
    assert set(ai_engine.REQUIRED_PROMPT_KEYS).issubset(ai_engine.PROMPTS)
    assert "首席情绪陪伴师" in ai_engine.PROMPTS["empathy_text"]
    assert "只返回 JSON" in ai_engine.PROMPTS["suggested_tags"]


def test_normalize_route_result_uses_default_island():
    result = ai_engine._normalize_route_result({"Island": "UNKNOWN", "Intensity": "LOW"})
    assert result["Island"] == DEFAULT_ISLAND_KEY
    assert result["Intensity"] == "LOW"
    assert DEFAULT_ISLAND_KEY in ISLAND_KEYS


def test_stream_empathy_text_yields_safe_fallback_on_connection_error(monkeypatch):
    async def _raise(*args, **kwargs):
        raise APIConnectionError(request=httpx.Request("POST", "https://example.com"))

    monkeypatch.setattr(ai_engine.client.chat.completions, "create", _raise)

    async def _collect():
        return [chunk async for chunk in ai_engine.stream_empathy_text("今天很乱")]

    chunks = asyncio.run(_collect())
    assert chunks == [ai_engine._safe_fallback_reply()]
