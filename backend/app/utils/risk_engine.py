import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Optional

from dotenv import load_dotenv
from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv("DASHSCOPE_BASE_URL")
RISK_MODEL_NAME = os.getenv("RISK_MODEL_NAME") or os.getenv("AI_MODEL_NAME")
RISK_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_RISK_SECONDS", "5"))

client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL) if API_KEY and BASE_URL else None

RISK_SYSTEM_PROMPT = """你是“言屿（AnimaIsle）”的风险判断中枢，只负责判断是否存在轻生、自杀、自残或严重暴力风险。

输出必须是合法 JSON，不要输出任何其他内容：
{
  "level": "SAFE | REVIEW | DANGER",
  "reason_code": "self_harm_intent | self_harm_history | violent_intent | ambiguous_distress | none"
}

判定规则：
1. 明确表达想死、想自杀、准备自残、描述方法/计划/时间地点，输出 DANGER。
2. 明确严重暴力伤人计划，输出 DANGER。
3. 只是情绪宣泄、崩溃、活着好累、我不想上班了、我想消失一下、好想逃开，但没有明确伤害计划，输出 REVIEW。
4. 普通负面情绪、难过、焦虑、失恋、委屈、压力大，输出 SAFE。
"""


@dataclass
class RiskCheckResult:
    level: str
    hit_type: str
    reason_code: str
    should_block: bool


class RiskEngineError(Exception):
    def __init__(self, code: str, stage: str, message: str, *, cause: Optional[Exception] = None):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.message = message
        self.cause = cause


DANGER_PATTERNS = [
    (re.compile(r"(自杀|自殘|自残|轻生|结束生命|不想活了|活不下去|去死)"), "self_harm_intent"),
    (re.compile(r"(割腕|跳楼|上吊|吞药|吞安眠药|烧炭|撞车|卧轨)"), "self_harm_intent"),
    (re.compile(r"(杀了他|杀了她|砍死|捅死|报复社会|炸了|伤害别人)"), "violent_intent"),
]

REVIEW_PATTERNS = [
    (re.compile(r"(想消失|想逃开|活着好累|不如死了算了|不想撑了|撑不住了|想离开这个世界)"), "ambiguous_distress"),
]


def _log(log_level: int, event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.log(log_level, json.dumps(payload, ensure_ascii=False, default=str))


def _rule_based_check(text: str, trace_id: Optional[str]) -> RiskCheckResult:
    for pattern, reason_code in DANGER_PATTERNS:
        if pattern.search(text):
            result = RiskCheckResult(level="DANGER", hit_type="rule", reason_code=reason_code, should_block=True)
            _log(logging.WARNING, "risk.rule.hit", trace_id=trace_id, level=result.level, reason_code=reason_code)
            return result

    for pattern, reason_code in REVIEW_PATTERNS:
        if pattern.search(text):
            result = RiskCheckResult(level="REVIEW", hit_type="rule", reason_code=reason_code, should_block=False)
            _log(logging.INFO, "risk.rule.hit", trace_id=trace_id, level=result.level, reason_code=reason_code)
            return result

    return RiskCheckResult(level="SAFE", hit_type="rule", reason_code="none", should_block=False)


def _normalize_level(level: str, default: str = "REVIEW") -> str:
    upper = (level or "").strip().upper()
    if upper in {"SAFE", "REVIEW", "DANGER"}:
        return upper
    return default


async def _model_check(text: str, trace_id: Optional[str], *, stage: str, hit_type: str) -> RiskCheckResult:
    if client is None:
        raise RiskEngineError("risk_model_unavailable", stage, "risk model client unavailable")

    started = time.perf_counter()
    _log(
        logging.INFO,
        "risk.model.start",
        trace_id=trace_id,
        stage=stage,
        text_len=len(text),
    )
    try:
        response = await client.chat.completions.create(
            model=RISK_MODEL_NAME,
            messages=[
                {"role": "system", "content": RISK_SYSTEM_PROMPT},
                {"role": "user", "content": f"用户输入：{text[:1500]}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=60,
            timeout=RISK_TIMEOUT_SECONDS,
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        level = _normalize_level(str(data.get("level") or "REVIEW"))
        reason_code = str(data.get("reason_code") or "ambiguous_distress")
        result = RiskCheckResult(
            level=level,
            hit_type=hit_type,
            reason_code=reason_code,
            should_block=(level == "DANGER"),
        )
        _log(
            logging.INFO,
            "risk.model.success",
            trace_id=trace_id,
            stage=stage,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
            level=result.level,
            reason_code=result.reason_code,
            hit_type=hit_type,
        )
        return result
    except json.JSONDecodeError as exc:
        _log(
            logging.ERROR,
            "risk.model.parse_failed",
            trace_id=trace_id,
            stage=stage,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise RiskEngineError("ai_parse_failed", stage, "risk model parse failed", cause=exc) from exc
    except APITimeoutError as exc:
        _log(
            logging.ERROR,
            "risk.model.timeout",
            trace_id=trace_id,
            stage=stage,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise RiskEngineError("ai_timeout", stage, "risk model timed out", cause=exc) from exc
    except (APIConnectionError, APIError) as exc:
        _log(
            logging.ERROR,
            "risk.model.api_failed",
            trace_id=trace_id,
            stage=stage,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise RiskEngineError("ai_api_failed", stage, "risk model API failed", cause=exc) from exc
    except Exception as exc:
        _log(
            logging.ERROR,
            "risk.model.failed",
            trace_id=trace_id,
            stage=stage,
            elapsed_ms=int((time.perf_counter() - started) * 1000),
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise RiskEngineError("risk_model_failed", stage, "risk model failed", cause=exc) from exc


async def check_text_risk(text: str, *, trace_id: Optional[str] = None) -> RiskCheckResult:
    rule_result = _rule_based_check(text, trace_id)

    if rule_result.level == "DANGER":
        _log(logging.WARNING, "risk.result", trace_id=trace_id, **asdict(rule_result))
        return rule_result

    try:
        model_result = await _model_check(text, trace_id, stage="risk_model_primary", hit_type="model")
    except RiskEngineError as exc:
        _log(
            logging.WARNING,
            "risk.result",
            trace_id=trace_id,
            level=rule_result.level,
            hit_type=rule_result.hit_type,
            reason_code=rule_result.reason_code,
            should_block=rule_result.should_block,
            fallback_reason=exc.code,
        )
        return rule_result

    if rule_result.level == "REVIEW" and model_result.level == "SAFE":
        result = RiskCheckResult(level="REVIEW", hit_type="fallback_llm", reason_code=rule_result.reason_code, should_block=False)
        _log(logging.INFO, "risk.result", trace_id=trace_id, **asdict(result))
        return result

    if rule_result.level == "SAFE" and model_result.level == "DANGER":
        fallback_result = await _model_check(text, trace_id, stage="risk_model_fallback", hit_type="fallback_llm")
        _log(logging.INFO, "risk.result", trace_id=trace_id, **asdict(fallback_result))
        return fallback_result

    _log(logging.INFO, "risk.result", trace_id=trace_id, **asdict(model_result))
    return model_result
