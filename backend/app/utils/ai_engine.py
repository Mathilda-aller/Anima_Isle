import base64
import hashlib
import json
import logging
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from dotenv import load_dotenv
from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI
from tenacity import RetryCallState, retry, stop_after_attempt, wait_exponential

from app.constants.islands import DEFAULT_ISLAND_KEY, DEFAULT_RECOMMENDED_TAGS

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv("DASHSCOPE_BASE_URL")
MODEL_NAME = os.getenv("AI_MODEL_NAME")
ASR_MODEL_NAME = os.getenv("ASR_MODEL_NAME", "qwen3-asr-flash")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-v4")

EMPATHY_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_EMPATHY_SECONDS", "8"))
ROUTER_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_ROUTER_SECONDS", "6"))
POEM_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_POEM_SECONDS", "8"))
TAG_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_TAG_SECONDS", "5"))
EMBEDDING_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_EMBEDDING_SECONDS", "6"))
ASR_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_ASR_SECONDS", "15"))

if not API_KEY or not BASE_URL:
    logger.critical("❌ Missing DashScope configuration in .env")
    raise ValueError("Missing DashScope configuration")

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)

REQUIRED_PROMPT_KEYS = ("empathy_text", "emotion_route", "three_line_poem", "suggested_tags")


def _load_prompts_from_json() -> Dict[str, str]:
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    json_path = os.path.join(backend_dir, "data", "ai_prompts.json")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_prompts = json.load(f)
    except Exception as exc:
        logger.critical("Failed to load AI prompts from %s: %s", json_path, exc)
        raise ValueError("Failed to load AI prompts") from exc

    if not isinstance(raw_prompts, dict):
        raise ValueError("AI prompts config must be a JSON object")

    prompts: Dict[str, str] = {}
    for key in REQUIRED_PROMPT_KEYS:
        value = raw_prompts.get(key)
        if not isinstance(value, list) or not all(isinstance(line, str) for line in value):
            raise ValueError(f"AI prompt '{key}' must be a list of strings")
        prompts[key] = "\n".join(value)

    return prompts


PROMPTS = _load_prompts_from_json()

ROUTE_INTENSITY_RULES: Dict[str, tuple[str, ...]] = {
    "THUNDER": ("HIGH", "LOW"),
    "MIST": ("HIGH", "LOW"),
    "CLOUD": ("HIGH", "LOW"),
    "RAIN": ("HIGH", "MODERATE", "LOW"),
    "SNOW": ("HIGH", "MODERATE", "LOW"),
    "WIND": ("HIGH", "MODERATE", "LOW"),
    "LIGHT": ("HIGH", "MODERATE", "LOW"),
}


class AIEngineError(Exception):
    def __init__(self, code: str, stage: str, message: str, *, cause: Optional[Exception] = None):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.message = message
        self.cause = cause


def _safe_fallback_reply() -> str:
    return "收到你这一刻的心事了，能把这些说出来已经很不容易。这样的重量落在谁身上，心里都会起潮，你现在的乱和钝都很真实。像言屿傍晚忽然压低的雾，风贴着海面绕过礁石，把没说完的话都吹成潮湿的回声。先在这片雾里坐一会儿也没关系，今天不用急着把自己整理好。"


def _safe_fallback_poem() -> str:
    return "海面的微光把夜色折细\n心事在风里慢慢长出回声\n你可以先把自己放在这里"


def _text_meta(text: str) -> Dict[str, Any]:
    return {
        "text_len": len(text),
        "text_preview": text[:50],
        "text_sha256_12": hashlib.sha256(text.encode("utf-8")).hexdigest()[:12],
    }


def _log_ai_event(log_level: int, event: str, **fields: Any) -> None:
    logger.log(log_level, json.dumps({"event": event, **fields}, ensure_ascii=False, default=str))


def _retry_before_sleep(retry_state: RetryCallState) -> None:
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    _log_ai_event(
        logging.WARNING,
        "ai.retry",
        stage=getattr(exc, "stage", None) if exc else None,
        code=getattr(exc, "code", None) if exc else None,
        attempt=retry_state.attempt_number,
        next_sleep_s=retry_state.next_action.sleep if retry_state.next_action else None,
        error_type=type(exc).__name__ if exc else None,
        error_message=str(exc) if exc else None,
    )


def _extract_text_content(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts).strip()
    return ""


def _normalize_recommended_tags(raw_tags: Optional[List[str]]) -> List[str]:
    tags: List[str] = []
    if isinstance(raw_tags, list):
        for item in raw_tags:
            if not isinstance(item, str):
                continue
            tag = item.strip()
            if not tag:
                continue
            tags.append(tag if tag.startswith("#") else f"#{tag}")

    deduped: List[str] = []
    seen = set()
    for tag in tags:
        if tag in seen:
            continue
        deduped.append(tag)
        seen.add(tag)

    for tag in DEFAULT_RECOMMENDED_TAGS:
        if len(deduped) >= 5:
            break
        if tag not in seen:
            deduped.append(tag)
            seen.add(tag)

    return deduped[:5]


def _normalize_route_result(data: Dict[str, object]) -> Dict[str, str]:
    island = str(data.get("Island") or "").strip().upper()
    intensity = str(data.get("Intensity") or "").strip().upper()

    if island not in ROUTE_INTENSITY_RULES:
        island = DEFAULT_ISLAND_KEY

    if intensity not in ROUTE_INTENSITY_RULES.get(island, ()):
        allowed = ROUTE_INTENSITY_RULES.get(island, ("LOW",))
        intensity = "LOW" if "LOW" in allowed else allowed[0]

    return {"Island": island, "Intensity": intensity}


def _normalize_poem_lines(content: str) -> str:
    lines = [line.strip() for line in (content or "").splitlines() if line.strip()]
    if len(lines) >= 3:
        return "\n".join(lines[:3])
    return _safe_fallback_poem()


def _render_prompt(prompt: str, **values: str) -> str:
    rendered = prompt
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


async def _create_chat_completion(
    *,
    stage: str,
    trace_id: Optional[str],
    text: str,
    timeout_seconds: float,
    **kwargs: Any,
) -> Any:
    started = time.perf_counter()
    meta = _text_meta(text)
    _log_ai_event(logging.INFO, "ai.request.start", trace_id=trace_id, stage=stage, timeout_s=timeout_seconds, **meta)
    try:
        response = await client.chat.completions.create(timeout=timeout_seconds, **kwargs)
        _log_ai_event(logging.INFO, "ai.request.success", trace_id=trace_id, stage=stage, elapsed_ms=int((time.perf_counter() - started) * 1000), **meta)
        return response
    except APITimeoutError as exc:
        _log_ai_event(logging.ERROR, "ai.request.timeout", trace_id=trace_id, stage=stage, elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc), **meta)
        raise AIEngineError("ai_timeout", stage, f"{stage} timed out", cause=exc) from exc
    except APIConnectionError as exc:
        _log_ai_event(logging.ERROR, "ai.request.connection_error", trace_id=trace_id, stage=stage, elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc), **meta)
        raise AIEngineError("ai_connection_failed", stage, f"{stage} connection failed", cause=exc) from exc
    except APIError as exc:
        _log_ai_event(logging.ERROR, "ai.request.api_error", trace_id=trace_id, stage=stage, elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc), **meta)
        raise AIEngineError("ai_api_failed", stage, f"{stage} API failed", cause=exc) from exc
    except Exception as exc:
        _log_ai_event(logging.ERROR, "ai.request.unexpected_error", trace_id=trace_id, stage=stage, elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc), **meta)
        raise AIEngineError("ai_unknown_failed", stage, f"{stage} failed", cause=exc) from exc


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True, before_sleep=_retry_before_sleep)
async def get_embedding(text: str, *, trace_id: Optional[str] = None) -> List[float]:
    started = time.perf_counter()
    meta = _text_meta(text)
    _log_ai_event(logging.INFO, "embedding.start", trace_id=trace_id, stage="embedding", **meta)
    try:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL_NAME,
            input=text[:8000],
            dimensions=1024,
            encoding_format="float",
            timeout=EMBEDDING_TIMEOUT_SECONDS,
        )
        _log_ai_event(logging.INFO, "embedding.success", trace_id=trace_id, stage="embedding", elapsed_ms=int((time.perf_counter() - started) * 1000), dimensions=len(response.data[0].embedding), **meta)
        return response.data[0].embedding
    except APITimeoutError as exc:
        _log_ai_event(logging.ERROR, "embedding.timeout", trace_id=trace_id, stage="embedding", elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc), **meta)
        raise AIEngineError("ai_timeout", "embedding", "embedding timed out", cause=exc) from exc
    except APIError as exc:
        _log_ai_event(logging.ERROR, "embedding.api_error", trace_id=trace_id, stage="embedding", elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc), **meta)
        raise AIEngineError("ai_api_failed", "embedding", "embedding API failed", cause=exc) from exc
    except Exception as exc:
        _log_ai_event(logging.ERROR, "embedding.failed", trace_id=trace_id, stage="embedding", elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc), **meta)
        raise AIEngineError("embedding_failed", "embedding", "embedding failed", cause=exc) from exc


async def stream_empathy_text(text: str, *, trace_id: Optional[str] = None) -> AsyncIterator[str]:
    meta = _text_meta(text)
    started = time.perf_counter()
    _log_ai_event(logging.INFO, "empathy.stream.start", trace_id=trace_id, stage="empathy_stream", timeout_s=EMPATHY_TIMEOUT_SECONDS, **meta)
    try:
        stream = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": PROMPTS["empathy_text"]},
                {"role": "user", "content": f"用户当前的倾诉内容：{text[:2000]}"},
            ],
            temperature=0.7,
            max_tokens=220,
            stream=True,
            timeout=EMPATHY_TIMEOUT_SECONDS,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if isinstance(delta, str) and delta:
                yield delta
            elif isinstance(delta, list):
                for item in delta:
                    if isinstance(item, dict) and item.get("type") == "text":
                        value = item.get("text")
                        if isinstance(value, str) and value:
                            yield value
        _log_ai_event(logging.INFO, "empathy.stream.success", trace_id=trace_id, stage="empathy_stream", elapsed_ms=int((time.perf_counter() - started) * 1000), **meta)
    except Exception as exc:
        _log_ai_event(logging.ERROR, "empathy.stream.failed", trace_id=trace_id, stage="empathy_stream", elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc), **meta)
        yield _safe_fallback_reply()


@retry(stop=stop_after_attempt(2), before_sleep=_retry_before_sleep, reraise=True)
async def classify_emotion_route(text: str, *, trace_id: Optional[str] = None) -> Dict[str, str]:
    try:
        response = await _create_chat_completion(
            stage="emotion_route",
            trace_id=trace_id,
            text=text,
            timeout_seconds=ROUTER_TIMEOUT_SECONDS,
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": _render_prompt(PROMPTS["emotion_route"], user_input=text[:2000])},
                {"role": "user", "content": f"用户当前的倾诉内容：{text[:2000]}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=80,
        )
        content = _extract_text_content(response.choices[0].message.content)
        try:
            return _normalize_route_result(json.loads(content))
        except json.JSONDecodeError as exc:
            _log_ai_event(logging.ERROR, "emotion_route.parse_failed", trace_id=trace_id, stage="emotion_route", error_type=type(exc).__name__, error_message=str(exc), response_preview=content[:120], **_text_meta(text))
            raise AIEngineError("ai_parse_failed", "emotion_route", "emotion route parse failed", cause=exc) from exc
    except AIEngineError:
        raise
    except Exception as exc:
        _log_ai_event(logging.ERROR, "emotion_route.failed", trace_id=trace_id, stage="emotion_route", error_type=type(exc).__name__, error_message=str(exc), **_text_meta(text))
        raise AIEngineError("ai_unknown_failed", "emotion_route", "emotion route failed", cause=exc) from exc


@retry(stop=stop_after_attempt(2), before_sleep=_retry_before_sleep, reraise=True)
async def generate_three_line_poem(user_input: str, image_description: str, *, trace_id: Optional[str] = None) -> str:
    combo = f"{user_input}\n{image_description}"
    try:
        response = await _create_chat_completion(
            stage="three_line_poem",
            trace_id=trace_id,
            text=combo,
            timeout_seconds=POEM_TIMEOUT_SECONDS,
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": _render_prompt(
                        PROMPTS["three_line_poem"],
                        user_input=user_input[:2000],
                        image_description=image_description[:200],
                    ),
                },
                {"role": "user", "content": f"用户心境：{user_input[:2000]}\n图片白描：{image_description[:200]}"},
            ],
            temperature=0.9,
            max_tokens=120,
        )
        return _normalize_poem_lines(_extract_text_content(response.choices[0].message.content))
    except AIEngineError:
        raise
    except Exception as exc:
        _log_ai_event(logging.ERROR, "three_line_poem.failed", trace_id=trace_id, stage="three_line_poem", error_type=type(exc).__name__, error_message=str(exc), **_text_meta(combo))
        raise AIEngineError("ai_unknown_failed", "three_line_poem", "three line poem failed", cause=exc) from exc


@retry(stop=stop_after_attempt(2), before_sleep=_retry_before_sleep, reraise=True)
async def generate_suggested_tags(text: str, *, trace_id: Optional[str] = None) -> List[str]:
    try:
        response = await _create_chat_completion(
            stage="suggested_tags",
            trace_id=trace_id,
            text=text,
            timeout_seconds=TAG_TIMEOUT_SECONDS,
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": PROMPTS["suggested_tags"]},
                {"role": "user", "content": f"用户心事: {text[:500]}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=120,
        )
        content = _extract_text_content(response.choices[0].message.content)
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            _log_ai_event(logging.ERROR, "suggested_tags.parse_failed", trace_id=trace_id, stage="suggested_tags", error_type=type(exc).__name__, error_message=str(exc), response_preview=content[:120], **_text_meta(text))
            raise AIEngineError("ai_parse_failed", "suggested_tags", "suggested tags parse failed", cause=exc) from exc
        if isinstance(data, list):
            return _normalize_recommended_tags(data)
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    return _normalize_recommended_tags(value)
        _log_ai_event(logging.WARNING, "suggested_tags.fallback_tags", trace_id=trace_id, stage="suggested_tags", reason="json_without_list", **_text_meta(text))
        return DEFAULT_RECOMMENDED_TAGS.copy()
    except AIEngineError:
        raise
    except Exception as exc:
        _log_ai_event(logging.ERROR, "suggested_tags.failed", trace_id=trace_id, stage="suggested_tags", error_type=type(exc).__name__, error_message=str(exc), **_text_meta(text))
        raise AIEngineError("ai_unknown_failed", "suggested_tags", "suggested tags failed", cause=exc) from exc


@retry(stop=stop_after_attempt(2), before_sleep=_retry_before_sleep, reraise=True)
async def transcribe_audio(
    audio_bytes: bytes,
    mime_type: str = "audio/webm",
    language: str = "zh",
    *,
    trace_id: Optional[str] = None,
) -> str:
    started = time.perf_counter()
    _log_ai_event(logging.INFO, "asr.start", trace_id=trace_id, stage="audio_transcription", mime_type=mime_type, audio_size_bytes=len(audio_bytes), timeout_s=ASR_TIMEOUT_SECONDS)
    try:
        if not audio_bytes:
            raise ValueError("Empty audio payload")

        encoded = base64.b64encode(audio_bytes).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{encoded}"
        completion = await client.chat.completions.create(
            model=ASR_MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {"data": data_uri},
                        }
                    ],
                }
            ],
            stream=False,
            timeout=ASR_TIMEOUT_SECONDS,
            extra_body={"asr_options": {"language": language, "enable_itn": False}},
        )
        text = _extract_text_content(completion.choices[0].message.content)
        if not text:
            raise ValueError("Empty transcription result")
        _log_ai_event(logging.INFO, "asr.success", trace_id=trace_id, stage="audio_transcription", elapsed_ms=int((time.perf_counter() - started) * 1000), transcript_len=len(text))
        return text
    except APITimeoutError as exc:
        _log_ai_event(logging.ERROR, "asr.timeout", trace_id=trace_id, stage="audio_transcription", elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc))
        raise AIEngineError("ai_timeout", "audio_transcription", "audio transcription timed out", cause=exc) from exc
    except APIError as exc:
        _log_ai_event(logging.ERROR, "asr.api_error", trace_id=trace_id, stage="audio_transcription", elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc))
        raise AIEngineError("ai_api_failed", "audio_transcription", "audio transcription API failed", cause=exc) from exc
    except Exception as exc:
        _log_ai_event(logging.ERROR, "asr.failed", trace_id=trace_id, stage="audio_transcription", elapsed_ms=int((time.perf_counter() - started) * 1000), error_type=type(exc).__name__, error_message=str(exc))
        raise AIEngineError("audio_transcription_failed", "audio_transcription", "audio transcription failed", cause=exc) from exc
