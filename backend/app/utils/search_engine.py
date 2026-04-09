# app/utils/search_engine.py
import os
import logging
from typing import List, Optional, Dict, Any

from pymilvus import MilvusClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ================= 配置部分 =================
ZILLIZ_URI = os.getenv("ZILLIZ_ENDPOINT")
ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN")
COLLECTION_NAME = "anima_isle"
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "https://anima-isle-images.oss-cn-beijing.aliyuncs.com").rstrip("/")

# COSINE 分数阈值，低于则认为不够相关
MIN_DISTANCE_THRESHOLD = 0.35

client: Optional[MilvusClient] = None
client_init_attempted = False


def _get_client() -> Optional[MilvusClient]:
    global client, client_init_attempted

    if client is not None:
        return client

    if client_init_attempted:
        return None

    client_init_attempted = True

    if not ZILLIZ_URI or not ZILLIZ_TOKEN:
        logger.critical("❌ Missing Zilliz configuration in .env")
        return None

    try:
        client = MilvusClient(uri=ZILLIZ_URI, token=ZILLIZ_TOKEN)
        logger.info("✅ Connected to Zilliz Cloud")
        return client
    except Exception as e:
        logger.critical(f"❌ Failed to connect to Zilliz: {str(e)}")
        return None


def get_fallback_result() -> Dict[str, Any]:
    """旧接口兜底结构（兼容）"""
    fallback_urls = _fallback_image_urls()
    return {
        "image_id": None,
        "poem": "迷雾笼罩\n我看清了你的心\n却看不清路",
        "semantic_text": None,
        "styles": {
            "A": fallback_urls[0],
            "B": fallback_urls[1],
            "C": fallback_urls[2],
        },
        "distance": None,
        "is_fallback": True,
    }


def _fallback_image_urls() -> List[str]:
    return [
        f"{IMAGE_BASE_URL}/RAIN_LOW/RAIN_LOW_00002.png",
        f"{IMAGE_BASE_URL}/LIGHT_LOW/LIGHT_LOW_00014.png",
        f"{IMAGE_BASE_URL}/THUNDER_HIGH/THUNDER_HIGH_00007.png",
    ]


def _static_fallback_candidates() -> List[Dict[str, Any]]:
    poem = "迷雾笼罩\n我看清了你的心\n却看不清路"
    fallback_urls = _fallback_image_urls()
    return [
        {
            "image_id": None,
            "image_url": fallback_urls[0],
            "poem_content": poem,
            "image_description": "海面的雾与微光",
            "emotion_intensity": "LOW",
            "semantic_text": "fallback",
            "distance": None,
            "is_fallback": True,
        },
        {
            "image_id": None,
            "image_url": fallback_urls[1],
            "poem_content": poem,
            "image_description": "海面的雾与微光",
            "emotion_intensity": "LOW",
            "semantic_text": "fallback",
            "distance": None,
            "is_fallback": True,
        },
        {
            "image_id": None,
            "image_url": fallback_urls[2],
            "poem_content": poem,
            "image_description": "海面的雾与微光",
            "emotion_intensity": "LOW",
            "semantic_text": "fallback",
            "distance": None,
            "is_fallback": True,
        },
    ]


def _coerce_image_url(entity: Dict[str, Any]) -> str:
    image_id = entity.get("Image_ID")
    if isinstance(image_id, str) and image_id.startswith("http"):
        return image_id

    direct_url = entity.get("image_url")
    if isinstance(direct_url, str) and direct_url:
        return direct_url

    # 新库当前约定 Image_ID 为图片名称；这里做保底映射，避免空 url
    if isinstance(image_id, str) and image_id:
        return image_id

    return _fallback_image_urls()[0]


def _normalize_candidate(hit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    entity = hit.get("entity") or {}
    distance = hit.get("distance")

    if distance is not None and distance < MIN_DISTANCE_THRESHOLD:
        return None

    poem_content = entity.get("poem_content") or "风吹过了海面\n你的心事被听见\n今夜请先休息"
    return {
        "image_id": str(entity.get("Image_ID")) if entity.get("Image_ID") is not None else None,
        "image_url": _coerce_image_url(entity),
        "poem_content": poem_content,
        "image_description": entity.get("Image_Description"),
        "emotion_intensity": entity.get("Emotion_Intensity"),
        "semantic_text": entity.get("Semantic_text"),
        "distance": distance,
        "is_fallback": (entity.get("Fallback_level") == 0),
    }


def _search_by_filter(vector: List[float], query_filter: str, limit: int) -> List[Dict[str, Any]]:
    current_client = _get_client()
    if current_client is None:
        return []

    results = current_client.search(
        collection_name=COLLECTION_NAME,
        data=[vector],
        limit=limit,
        filter=query_filter,
        output_fields=[
            "Image_ID",
            "Island_Target",
            "Emotion_Intensity",
            "Image_Description",
            "Semantic_text",
            "poem_content",
            "Fallback_level",
            "image_url",
        ],
    )
    if not results or len(results) == 0:
        return []
    return results[0]


def _append_candidates(
    selected: List[Dict[str, Any]],
    seen_image_ids: set,
    hits: List[Dict[str, Any]],
    top_k: int,
) -> None:
    for hit in hits:
        candidate = _normalize_candidate(hit)
        if not candidate:
            continue
        image_id = candidate.get("image_id")
        if image_id and image_id in seen_image_ids:
            continue
        selected.append(candidate)
        if image_id:
            seen_image_ids.add(image_id)
        if len(selected) >= top_k:
            return


def search_island_candidates(
    vector: List[float],
    island_target: str,
    intensity: Optional[str] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    三段退让：
    1. 先查同岛 + 同强度的非兜底图
    2. 不足再查同岛的非兜底图
    3. 最后才补 OSS 静态兜底图
    """
    if not vector:
        logger.warning("⚠️ Island search triggered with empty vector")
        return _static_fallback_candidates()[:top_k]

    try:
        selected: List[Dict[str, Any]] = []
        seen_image_ids = set()

        # 第 1 轮：同岛 + 同强度
        if intensity:
            primary_filter = f'Island_Target == "{island_target}" and Emotion_Intensity == "{intensity}" and Fallback_level == 1'
            primary_hits = _search_by_filter(vector, primary_filter, limit=max(top_k * 2, top_k))
            _append_candidates(selected, seen_image_ids, primary_hits, top_k)

        # 第 2 轮：只按同岛
        if len(selected) < top_k:
            island_only_filter = f'Island_Target == "{island_target}" and Fallback_level == 1'
            island_only_hits = _search_by_filter(vector, island_only_filter, limit=max(top_k * 3, top_k))
            _append_candidates(selected, seen_image_ids, island_only_hits, top_k)

        # 第 3 轮：OSS 静态补齐
        if len(selected) < top_k:
            for item in _static_fallback_candidates():
                image_id = item.get("image_id")
                if image_id and image_id in seen_image_ids:
                    continue
                selected.append(item)
                if image_id:
                    seen_image_ids.add(image_id)
                if len(selected) >= top_k:
                    break

        # 按 distance 排序（None 放最后）
        selected.sort(key=lambda x: (x.get("distance") is None, -(x.get("distance") or 0)))
        return selected[:top_k]

    except Exception as e:
        logger.error(f"❌ Zilliz Island Search Error: {str(e)}", exc_info=True)
        return _static_fallback_candidates()[:top_k]


def search_visual_match(vector: List[float], top_k: int = 1) -> Optional[Dict[str, Any]]:
    """
    旧版兼容接口：用于 style A/B/C 逻辑，保留避免外部调用崩溃。
    """
    if not vector:
        logger.warning("⚠️ Search triggered with empty vector")
        return get_fallback_result()

    try:
        current_client = _get_client()
        if current_client is None:
            return get_fallback_result()

        results = current_client.search(
            collection_name=COLLECTION_NAME,
            data=[vector],
            limit=top_k,
            output_fields=[
                "id",
                "poem",
                "semantic_text",
                "style_a_url",
                "style_b_url",
                "style_c_url",
            ],
        )

        if not results or len(results) == 0 or len(results[0]) == 0:
            logger.warning("⚠️ No visual match found in Zilliz.")
            return get_fallback_result()

        best_match = results[0][0]
        distance = best_match.get("distance")
        entity = best_match["entity"]

        if distance is None or distance < MIN_DISTANCE_THRESHOLD:
            logger.info(
                f"Best match distance {distance:.4f} below threshold {MIN_DISTANCE_THRESHOLD}, using fallback."
            )
            return get_fallback_result()

        logger.info(f"🔍 Search Success. ID: {entity.get('id')}, Score: {distance:.4f}")

        return {
            "image_id": str(entity.get("id")),
            "poem": entity.get("poem"),
            "semantic_text": entity.get("semantic_text"),
            "styles": {
                "A": entity.get("style_a_url"),
                "B": entity.get("style_b_url"),
                "C": entity.get("style_c_url"),
            },
            "distance": distance,
            "is_fallback": False,
        }

    except Exception as e:
        logger.error(f"❌ Zilliz Search Error: {str(e)}", exc_info=True)
        return get_fallback_result()


def get_distance_threshold() -> float:
    return MIN_DISTANCE_THRESHOLD
