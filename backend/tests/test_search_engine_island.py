from app.utils import search_engine


class _FakeClient:
    def __init__(self, intensity_hits, island_hits):
        self.intensity_hits = intensity_hits
        self.island_hits = island_hits

    def search(self, collection_name, data, limit, filter, output_fields):
        if "Emotion_Intensity" in filter:
            return [self.intensity_hits[:limit]]
        return [self.island_hits[:limit]]


def _hit(image_id: str, distance: float, fallback_level: int):
    return {
        "distance": distance,
        "entity": {
            "Image_ID": image_id,
            "Island_Target": "ISLAND_1",
            "Semantic_text": f"semantic-{image_id}",
            "poem_content": f"poem-{image_id}",
            "Fallback_level": fallback_level,
            "image_url": f"https://img/{image_id}.jpg",
        },
    }


def test_search_island_candidates_builds_oss_url_from_legacy_image_id(monkeypatch):
    fake_client = _FakeClient(
        intensity_hits=[
            {
                "distance": 0.91,
                "entity": {
                    "Image_ID": "MIST_LOW_00001",
                    "Island_Target": "MIST",
                    "Emotion_Intensity": "LOW",
                    "Semantic_text": "semantic",
                    "poem_content": "poem",
                    "Fallback_level": 1,
                },
            }
        ],
        island_hits=[],
    )
    monkeypatch.setattr(search_engine, "client", fake_client)
    monkeypatch.setattr(search_engine, "client_init_attempted", True)
    monkeypatch.setattr(search_engine, "IMAGE_BASE_URL", "https://oss.example.com")

    result = search_engine.search_island_candidates([0.1] * 1024, "MIST", intensity="LOW", top_k=1)

    assert result[0]["image_url"] == "https://oss.example.com/MIST_LOW/MIST_LOW_00001.png"


def test_search_island_candidates_primary_enough(monkeypatch):
    fake_client = _FakeClient(
        intensity_hits=[
            _hit("a", 0.91, 1),
            _hit("b", 0.88, 1),
            _hit("c", 0.82, 1),
        ],
        island_hits=[_hit("x", 0.70, 1)],
    )
    monkeypatch.setattr(search_engine, "client", fake_client)
    monkeypatch.setattr(search_engine, "client_init_attempted", True)

    result = search_engine.search_island_candidates([0.1] * 1024, "ISLAND_1", intensity="HIGH", top_k=3)
    assert len(result) == 3
    assert [item["image_id"] for item in result] == ["a", "b", "c"]
    assert all(item["is_fallback"] is False for item in result)


def test_search_island_candidates_fill_with_island_candidates(monkeypatch):
    fake_client = _FakeClient(
        intensity_hits=[_hit("a", 0.91, 1)],
        island_hits=[_hit("a", 0.91, 1), _hit("x", 0.80, 1), _hit("y", 0.79, 1)],
    )
    monkeypatch.setattr(search_engine, "client", fake_client)
    monkeypatch.setattr(search_engine, "client_init_attempted", True)

    result = search_engine.search_island_candidates([0.1] * 1024, "ISLAND_1", intensity="HIGH", top_k=3)
    assert len(result) == 3
    assert [item["image_id"] for item in result] == ["a", "x", "y"]
    assert all(item["is_fallback"] is False for item in result)


def test_search_island_candidates_static_oss_fallback(monkeypatch):
    fake_client = _FakeClient(intensity_hits=[], island_hits=[])
    monkeypatch.setattr(search_engine, "client", fake_client)
    monkeypatch.setattr(search_engine, "client_init_attempted", True)
    monkeypatch.setattr(search_engine, "IMAGE_BASE_URL", "https://oss.example.com")

    result = search_engine.search_island_candidates([0.1] * 1024, "ISLAND_1", intensity="HIGH", top_k=3)
    assert len(result) == 3
    assert all(item["is_fallback"] is True for item in result)
    assert all(item["image_url"].startswith("https://oss.example.com/") for item in result)


def test_get_client_retries_after_failure(monkeypatch):
    attempts = {"count": 0}

    class _RecoveredClient:
        pass

    def _factory(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary failure")
        return _RecoveredClient()

    monkeypatch.setattr(search_engine, "client", None)
    monkeypatch.setattr(search_engine, "client_init_attempted", False)
    monkeypatch.setattr(search_engine, "ZILLIZ_URI", "https://example.zilliz.com")
    monkeypatch.setattr(search_engine, "ZILLIZ_TOKEN", "token")
    monkeypatch.setattr(search_engine, "MilvusClient", _factory)

    assert search_engine._get_client() is None

    recovered = search_engine._get_client()
    assert isinstance(recovered, _RecoveredClient)
    assert attempts["count"] == 2


def test_search_island_candidates_recovers_after_initial_client_failure(monkeypatch):
    attempts = {"count": 0}
    recovered_client = _FakeClient(
        intensity_hits=[_hit("a", 0.91, 1), _hit("b", 0.88, 1), _hit("c", 0.82, 1)],
        island_hits=[],
    )

    def _factory(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary failure")
        return recovered_client

    monkeypatch.setattr(search_engine, "client", None)
    monkeypatch.setattr(search_engine, "client_init_attempted", False)
    monkeypatch.setattr(search_engine, "ZILLIZ_URI", "https://example.zilliz.com")
    monkeypatch.setattr(search_engine, "ZILLIZ_TOKEN", "token")
    monkeypatch.setattr(search_engine, "MilvusClient", _factory)

    first = search_engine.search_island_candidates([0.1] * 1024, "ISLAND_1", intensity="HIGH", top_k=3)
    second = search_engine.search_island_candidates([0.1] * 1024, "ISLAND_1", intensity="HIGH", top_k=3)

    assert all(item["is_fallback"] is True for item in first)
    assert [item["image_id"] for item in second] == ["a", "b", "c"]
    assert all(item["is_fallback"] is False for item in second)
    assert attempts["count"] == 2


def test_search_island_candidates_deduplicates_across_primary_and_island_hits(monkeypatch):
    fake_client = _FakeClient(
        intensity_hits=[_hit("a", 0.91, 1), _hit("b", 0.88, 1)],
        island_hits=[_hit("a", 0.91, 1), _hit("c", 0.80, 1), _hit("d", 0.79, 1)],
    )
    monkeypatch.setattr(search_engine, "client", fake_client)
    monkeypatch.setattr(search_engine, "client_init_attempted", True)

    result = search_engine.search_island_candidates([0.1] * 1024, "ISLAND_1", intensity="HIGH", top_k=3)

    assert [item["image_id"] for item in result] == ["a", "b", "c"]


def test_search_island_candidates_uses_static_fallback_only_when_all_hits_below_threshold(monkeypatch):
    fake_client = _FakeClient(
        intensity_hits=[_hit("a", 0.29, 1), _hit("b", 0.12, 1)],
        island_hits=[_hit("c", 0.28, 1), _hit("d", 0.05, 1)],
    )
    monkeypatch.setattr(search_engine, "client", fake_client)
    monkeypatch.setattr(search_engine, "client_init_attempted", True)
    monkeypatch.setattr(search_engine, "IMAGE_BASE_URL", "https://oss.example.com")

    result = search_engine.search_island_candidates([0.1] * 1024, "ISLAND_1", intensity="HIGH", top_k=3)

    assert len(result) == 3
    assert all(item["is_fallback"] is True for item in result)
    assert all(item["image_url"].startswith("https://oss.example.com/") for item in result)
