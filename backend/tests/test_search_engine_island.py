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
