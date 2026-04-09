import asyncio

import pytest
from app.constants.islands import DEFAULT_ISLAND_KEY, ISLAND_KEYS
from app.utils import ai_engine


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


def test_analyze_island_tags_and_reply_fallback(monkeypatch):
    async def _raise(*args, **kwargs):
        raise RuntimeError("mock llm error")

    monkeypatch.setattr(ai_engine.client.chat.completions, "create", _raise)

    with pytest.raises(ai_engine.AIEngineError):
        asyncio.run(ai_engine.analyze_island_tags_and_reply("今天很难过"))


def test_analyze_island_tags_and_reply_normalize(monkeypatch):
    async def _ok(*args, **kwargs):
        return _FakeResponse(
            '{"Island":"UNKNOWN","Intensity":"LOW"}'
        )

    monkeypatch.setattr(ai_engine.client.chat.completions, "create", _ok)

    async def _reply(*args, **kwargs):
        return "我在"

    async def _tags(*args, **kwargs):
        return ["孤独", "#焦虑", "#焦虑", "  ", "#雨夜"]

    monkeypatch.setattr(ai_engine, "generate_empathy_text", _reply)
    monkeypatch.setattr(ai_engine, "generate_suggested_tags", _tags)

    result = asyncio.run(ai_engine.analyze_island_tags_and_reply("今天很乱"))
    assert result["island_target"] == DEFAULT_ISLAND_KEY
    assert len(result["recommended_tags"]) == 5
    assert result["recommended_tags"][0] == "#孤独"
    assert all(tag.startswith("#") for tag in result["recommended_tags"])
    assert DEFAULT_ISLAND_KEY in ISLAND_KEYS
