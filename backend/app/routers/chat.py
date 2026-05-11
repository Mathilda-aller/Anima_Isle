import asyncio
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud, deps, models, schemas
from app.constants.islands import DEFAULT_RECOMMENDED_TAGS
from app.utils import ai_engine, risk_engine, search_engine
from app.utils.time import utc_now

logger = logging.getLogger(__name__)
router = APIRouter()
QUESTIONS_DB: Dict[str, List[str]] = {}
DisconnectChecker = Callable[[], Awaitable[bool]]
DAILY_TICKET_LIMIT = 2


def _log_chat_event(log_level: int, event: str, **fields: Any) -> None:
    logger.log(log_level, json.dumps({"event": event, **fields}, ensure_ascii=False, default=str))


def _build_error_detail(code: str, trace_id: str) -> str:
    return f"{code}|trace_id={trace_id}"


def _map_generation_error(exc: Exception) -> str:
    if isinstance(exc, ai_engine.AIEngineError):
        return exc.code
    if isinstance(exc, risk_engine.RiskEngineError):
        return exc.code

    message = str(exc).lower()
    if "ticket" in message or "commit" in message or "database" in message or "persist" in message:
        return "ticket_persist_failed"
    if "search" in message or "zilliz" in message or "milvus" in message:
        return "vector_search_failed"
    return "generation_failed"


def _is_mysql_unsupported_character_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "incorrect string value" in message or "1366" in message


def _stage_start(
    trace_id: str,
    session_id: str,
    user_id: int,
    step_name: str,
) -> float:
    _log_chat_event(
        logging.INFO,
        "chat.reply.stage.start",
        trace_id=trace_id,
        session_id=session_id,
        user_id=user_id,
        step_name=step_name,
    )
    return time.perf_counter()


def _stage_end(
    trace_id: str,
    session_id: str,
    user_id: int,
    breakdown: Dict[str, int],
    step_name: str,
    started_at: float,
    *,
    success: bool = True,
    **extra: Any,
) -> None:
    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    breakdown[step_name] = elapsed_ms
    _log_chat_event(
        logging.INFO if success else logging.ERROR,
        "chat.reply.stage.end",
        trace_id=trace_id,
        session_id=session_id,
        user_id=user_id,
        step_name=step_name,
        elapsed_ms=elapsed_ms,
        success=success,
        **extra,
    )


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


async def _never_disconnected() -> bool:
    return False


def _today_start() -> datetime:
    return utc_now().replace(hour=0, minute=0, second=0, microsecond=0)


def _assert_daily_ticket_limit_not_reached(
    *,
    db: Session,
    user: models.User,
) -> None:
    if user.is_internal_tester:
        return

    created_today = crud.count_user_tickets_created_since(
        db,
        user_id=user.id,
        since=_today_start(),
    )
    if created_today >= DAILY_TICKET_LIMIT:
        raise HTTPException(status_code=429, detail="daily_ticket_limit_reached")


async def _cancel_background_tasks(*tasks: Optional[asyncio.Task[Any]]) -> None:
    collected = [task for task in tasks if task is not None]
    for task in collected:
        if not task.done():
            task.cancel()
    if collected:
        await asyncio.gather(*collected, return_exceptions=True)


async def _raise_if_client_disconnected(is_disconnected: DisconnectChecker) -> None:
    if await is_disconnected():
        raise asyncio.CancelledError("client_disconnected")


def _log_parallel_task_failure(
    *,
    task: asyncio.Task[Any],
    trace_id: str,
    session_id: str,
    user_id: int,
    breakdown: Dict[str, int],
    step_name: str,
    started_at: float,
) -> None:
    if task.cancelled():
        _stage_end(
            trace_id,
            session_id,
            user_id,
            breakdown,
            step_name,
            started_at,
            success=False,
            error_code="cancelled",
            error_type="CancelledError",
            error_message="task cancelled",
        )
        return

    exc = task.exception()
    if exc is None:
        return

    _stage_end(
        trace_id,
        session_id,
        user_id,
        breakdown,
        step_name,
        started_at,
        success=False,
        error_code=_map_generation_error(exc),
        error_type=type(exc).__name__,
        error_message=str(exc),
    )


async def _await_route_and_embedding(
    *,
    route_task: asyncio.Task[Any],
    embedding_task: asyncio.Task[Any],
    trace_id: str,
    session_id: str,
    user_id: int,
    breakdown: Dict[str, int],
    route_started: float,
    embedding_started: float,
) -> tuple[Dict[str, Any], List[float]]:
    try:
        return await asyncio.gather(route_task, embedding_task)
    except BaseException:
        await _cancel_background_tasks(route_task, embedding_task)
        _log_parallel_task_failure(
            task=route_task,
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            breakdown=breakdown,
            step_name="emotion_route",
            started_at=route_started,
        )
        _log_parallel_task_failure(
            task=embedding_task,
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            breakdown=breakdown,
            step_name="embedding",
            started_at=embedding_started,
        )
        raise


async def _await_recommended_tags(
    *,
    tags_task: asyncio.Task[Any],
    trace_id: str,
    session_id: str,
    user_id: int,
    breakdown: Dict[str, int],
    tags_started: float,
) -> List[str]:
    try:
        tags = await tags_task
        normalized_tags = tags or DEFAULT_RECOMMENDED_TAGS.copy()
        _stage_end(
            trace_id,
            session_id,
            user_id,
            breakdown,
            "suggested_tags",
            tags_started,
            tag_count=len(normalized_tags),
            fallback=False,
        )
        return normalized_tags
    except Exception as exc:
        fallback_tags = DEFAULT_RECOMMENDED_TAGS.copy()
        logger.warning(
            "suggested_tags fallback used",
            extra={
                "trace_id": trace_id,
                "session_id": session_id,
                "user_id": user_id,
                "error_code": _map_generation_error(exc),
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        _stage_end(
            trace_id,
            session_id,
            user_id,
            breakdown,
            "suggested_tags",
            tags_started,
            tag_count=len(fallback_tags),
            fallback=True,
            error_code=_map_generation_error(exc),
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        return fallback_tags


def load_questions_from_json() -> None:
    global QUESTIONS_DB
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    json_path = os.path.join(root_dir, "data", "questions.json")

    try:
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                QUESTIONS_DB = json.load(f)
            logger.info("✅ [Startup] Loaded Questions: %s items.", len(QUESTIONS_DB.get("turn_1", [])))
        else:
            logger.warning("⚠️ [Startup] questions.json not found at %s", json_path)
            QUESTIONS_DB = {
                "turn_1": ["今天过得怎么样？", "此刻你的心情颜色是什么？"],
            }
    except Exception as exc:
        logger.error("❌ [Startup] Failed to load questions.json: %s", exc)
        QUESTIONS_DB = {
            "turn_1": ["System Error: Default Q1"],
        }


@router.post("/start", response_model=schemas.ChatStartResponse)
def start_chat(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    _assert_daily_ticket_limit_not_reached(db=db, user=current_user)
    chat_session = crud.create_chat_session(db, user_id=current_user.id)
    q1_list = QUESTIONS_DB.get("turn_1", ["今天发生了什么？"])
    first_q = random.choice(q1_list)
    logger.info("User %s started chat session %s", current_user.id, chat_session.session_id)
    return schemas.ChatStartResponse(session_id=chat_session.session_id, first_question=first_q)


@router.post("/transcribe", response_model=schemas.ChatVoiceTranscribeResponse)
async def transcribe_chat_audio(
    session_id: str = Form(...),
    duration: float = Form(0.0),
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    trace_id = uuid.uuid4().hex[:12]
    session = crud.get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    if session.current_step not in {0, 1}:
        raise HTTPException(status_code=409, detail="Session no longer accepts input")

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")
    mime_type = file.content_type or "audio/webm"
    if not mime_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid audio file type")

    try:
        transcript_text = await ai_engine.transcribe_audio(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            language="zh",
            trace_id=trace_id,
        )
    except Exception as exc:
        error_code = exc.code if isinstance(exc, ai_engine.AIEngineError) else "audio_transcription_failed"
        _log_chat_event(
            logging.ERROR,
            "chat.transcribe.failed",
            trace_id=trace_id,
            session_id=session_id,
            user_id=current_user.id,
            error_code=error_code,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise HTTPException(status_code=502, detail=_build_error_detail(error_code, trace_id))

    return schemas.ChatVoiceTranscribeResponse(
        session_id=session_id,
        text=transcript_text,
        duration=duration,
        is_final=True,
    )


def _write_ai_log(
    *,
    db: Session,
    trace_id: str,
    session_id: str,
    user_id: int,
    full_context: str,
    reply_text: str,
    risk_flag: bool,
    breakdown: Dict[str, int],
) -> None:
    ai_log_started = _stage_start(trace_id, session_id, user_id, "ai_log_write")
    try:
        ai_log = models.AIChatLog(
            session_id=session_id,
            user_id=user_id,
            user_full_input=full_context,
            ai_reply_content=reply_text,
            ai_risk_flag=risk_flag,
            ai_sentiment_score=None,
            duration_ms=sum(breakdown.values()) if breakdown else 0,
        )
        db.add(ai_log)
        db.commit()
        _stage_end(trace_id, session_id, user_id, breakdown, "ai_log_write", ai_log_started)
    except Exception as exc:
        _stage_end(
            trace_id,
            session_id,
            user_id,
            breakdown,
            "ai_log_write",
            ai_log_started,
            success=False,
            error_code="audit_log_failed_nonfatal",
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        db.rollback()


async def _generate_ticket_bundle(
    *,
    db: Session,
    session: models.ChatSession,
    current_user: models.User,
    full_context: str,
    trace_id: str,
    breakdown: Dict[str, int],
    reply_text: str,
) -> Dict[str, Any]:
    tags_started = _stage_start(trace_id, session.session_id, current_user.id, "suggested_tags")
    tags_task = asyncio.create_task(ai_engine.generate_suggested_tags(full_context, trace_id=trace_id))
    try:
        route_started = _stage_start(trace_id, session.session_id, current_user.id, "emotion_route")
        embedding_started = _stage_start(trace_id, session.session_id, current_user.id, "embedding")
        route_task = asyncio.create_task(ai_engine.classify_emotion_route(full_context, trace_id=trace_id))
        embedding_task = asyncio.create_task(ai_engine.get_embedding(full_context, trace_id=trace_id))

        route_result, vector = await _await_route_and_embedding(
            route_task=route_task,
            embedding_task=embedding_task,
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            breakdown=breakdown,
            route_started=route_started,
            embedding_started=embedding_started,
        )
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "emotion_route",
            route_started,
            island_target=route_result["Island"],
            intensity=route_result["Intensity"],
        )
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "embedding",
            embedding_started,
            vector_size=len(vector),
        )

        search_started = _stage_start(trace_id, session.session_id, current_user.id, "vector_search")
        candidate_images = search_engine.search_island_candidates(
            vector=vector,
            island_target=route_result["Island"],
            intensity=route_result["Intensity"],
            top_k=3,
        )
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "vector_search",
            search_started,
            candidate_count=len(candidate_images),
        )
        poem_started = _stage_start(trace_id, session.session_id, current_user.id, "three_line_poem")
        candidate_images = await _hydrate_candidate_poems(
            full_context=full_context,
            candidate_images=candidate_images,
            trace_id=trace_id,
        )
        primary = candidate_images[0]
        generated_poem = primary["poem_content"]
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "three_line_poem",
            poem_started,
        )
        recommended_tags = await _await_recommended_tags(
            tags_task=tags_task,
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            breakdown=breakdown,
            tags_started=tags_started,
        )

        ticket_payload = {
            "image_url": primary.get("image_url"),
            "poem_content": generated_poem,
            "image_style": None,
            "user_diary_summary": full_context,
            "island_category": route_result["Island"],
            "selected_image_id": primary.get("image_id"),
        }

        ticket_started = _stage_start(trace_id, session.session_id, current_user.id, "ticket_create")
        new_ticket = crud.create_ticket(db, ticket_payload, user_id=current_user.id)
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "ticket_create",
            ticket_started,
            ticket_uid=new_ticket.ticket_uid,
        )

        session_finish_started = _stage_start(trace_id, session.session_id, current_user.id, "session_finish")
        crud.update_chat_step(db, session.session_id, step=3)
        _stage_end(trace_id, session.session_id, current_user.id, breakdown, "session_finish", session_finish_started)

        _write_ai_log(
            db=db,
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            full_context=full_context,
            reply_text=reply_text,
            risk_flag=False,
            breakdown=breakdown,
        )

        return {
            "id": new_ticket.id,
            "ticket_uid": new_ticket.ticket_uid,
            "image_url": primary.get("image_url"),
            "poem_content": generated_poem,
            "island_category": route_result["Island"],
            "is_public": False,
            "created_at": new_ticket.created_at,
            "recommended_tags": recommended_tags,
            "candidate_images": candidate_images,
        }
    except BaseException:
        await _cancel_background_tasks(tags_task)
        raise


async def _save_turn_1_and_build_context(
    *,
    db: Session,
    session: models.ChatSession,
    reply_req: schemas.ChatReplyRequest,
    trace_id: str,
    user_id: int,
    breakdown: Dict[str, int],
) -> tuple[models.ChatSession, str]:
    save_input_started = _stage_start(trace_id, session.session_id, user_id, "save_input")
    try:
        session = crud.update_chat_step(
            db,
            session_id=session.session_id,
            step=1,
            answer=reply_req.content,
            turn_index=1,
        )
    except SQLAlchemyError as exc:
        if _is_mysql_unsupported_character_error(exc):
            _stage_end(
                trace_id,
                session.session_id,
                user_id,
                breakdown,
                "save_input",
                save_input_started,
                success=False,
                error_code="chat_contains_unsupported_characters",
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise HTTPException(status_code=400, detail="chat_contains_unsupported_characters") from exc
        raise
    _stage_end(trace_id, session.session_id, user_id, breakdown, "save_input", save_input_started)
    full_context = session.turn_1_answer or ""
    return session, full_context


async def _hydrate_candidate_poems(
    *,
    full_context: str,
    candidate_images: List[Dict[str, Any]],
    trace_id: str,
) -> List[Dict[str, Any]]:
    poems = await asyncio.gather(
        *[
            ai_engine.generate_three_line_poem(
                full_context,
                candidate.get("image_description") or "海面的雾与微光",
                trace_id=trace_id,
            )
            for candidate in candidate_images
        ]
    )
    return [{**candidate, "poem_content": poem} for candidate, poem in zip(candidate_images, poems)]


async def _build_sync_final_response(
    *,
    db: Session,
    session: models.ChatSession,
    current_user: models.User,
    full_context: str,
    trace_id: str,
    breakdown: Dict[str, int],
    request_started: float,
) -> schemas.ChatStepResponse:
    _log_chat_event(
        logging.WARNING,
        "chat.reply.compat_mode",
        trace_id=trace_id,
        session_id=session.session_id,
        user_id=current_user.id,
        mode="sync_final_generation",
    )

    risk_started = _stage_start(trace_id, session.session_id, current_user.id, "risk_check")
    risk_result = await risk_engine.check_text_risk(full_context, trace_id=trace_id)
    _stage_end(
        trace_id,
        session.session_id,
        current_user.id,
        breakdown,
        "risk_check",
        risk_started,
        level=risk_result.level,
        reason_code=risk_result.reason_code,
        should_block=risk_result.should_block,
        hit_type=risk_result.hit_type,
    )

    if risk_result.should_block:
        risk_reply_text = "我感觉到你现在非常痛苦，请允许我暂停一下... (风控拦截)"
        risk_finish_started = _stage_start(trace_id, session.session_id, current_user.id, "session_finish")
        crud.update_chat_step(db, session.session_id, step=2)
        _stage_end(trace_id, session.session_id, current_user.id, breakdown, "session_finish", risk_finish_started)
        _write_ai_log(
            db=db,
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            full_context=full_context,
            reply_text=risk_reply_text,
            risk_flag=True,
            breakdown=breakdown,
        )
        _log_chat_event(
            logging.WARNING,
            "chat.reply.request.end",
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            state="risk_blocked",
            elapsed_ms=int((time.perf_counter() - request_started) * 1000),
            breakdown=breakdown,
            mode="compat_sync",
        )
        return schemas.ChatStepResponse(session_id=session.session_id, state="risk_blocked", reply_text=risk_reply_text)

    empathy_started = _stage_start(trace_id, session.session_id, current_user.id, "empathy_text")
    try:
        reply_chunks: List[str] = []
        async for delta in ai_engine.stream_empathy_text(full_context, trace_id=trace_id):
            reply_chunks.append(delta)
        reply_text = "".join(reply_chunks).strip() or ai_engine._safe_fallback_reply()
        _stage_end(trace_id, session.session_id, current_user.id, breakdown, "empathy_text", empathy_started, reply_len=len(reply_text))
    except Exception as exc:
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "empathy_text",
            empathy_started,
            success=False,
            error_code=_map_generation_error(exc),
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
        raise

    ticket_data = await _generate_ticket_bundle(
        db=db,
        session=session,
        current_user=current_user,
        full_context=full_context,
        trace_id=trace_id,
        breakdown=breakdown,
        reply_text=reply_text,
    )
    _log_chat_event(
        logging.INFO,
        "chat.reply.request.end",
        trace_id=trace_id,
        session_id=session.session_id,
        user_id=current_user.id,
        state="finished",
        elapsed_ms=int((time.perf_counter() - request_started) * 1000),
        breakdown=breakdown,
        mode="compat_sync",
    )
    return schemas.ChatStepResponse(
        session_id=session.session_id,
        state="finished",
        reply_text=reply_text,
        ticket_data=ticket_data,
    )


async def _stream_final_reply_events(
    *,
    db: Session,
    session: models.ChatSession,
    current_user: models.User,
    full_context: str,
    trace_id: str,
    breakdown: Dict[str, int],
    request_started: float,
    is_disconnected: DisconnectChecker,
) -> AsyncIterator[str]:
    route_task: Optional[asyncio.Task[Any]] = None
    embedding_task: Optional[asyncio.Task[Any]] = None
    tags_task: Optional[asyncio.Task[Any]] = None

    try:
        await _raise_if_client_disconnected(is_disconnected)
        yield _sse_event("ack", {"session_id": session.session_id, "trace_id": trace_id})

        risk_started = _stage_start(trace_id, session.session_id, current_user.id, "risk_check")
        risk_result = await risk_engine.check_text_risk(full_context, trace_id=trace_id)
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "risk_check",
            risk_started,
            level=risk_result.level,
            reason_code=risk_result.reason_code,
            should_block=risk_result.should_block,
            hit_type=risk_result.hit_type,
        )

        await _raise_if_client_disconnected(is_disconnected)
        yield _sse_event(
            "risk",
            {
                "level": risk_result.level,
                "reason_code": risk_result.reason_code,
                "should_block": risk_result.should_block,
                "hit_type": risk_result.hit_type,
                "trace_id": trace_id,
            },
        )

        if risk_result.should_block:
            risk_reply_text = "我感觉到你现在非常痛苦，请允许我暂停一下... (风控拦截)"
            risk_finish_started = _stage_start(trace_id, session.session_id, current_user.id, "session_finish")
            crud.update_chat_step(db, session.session_id, step=2)
            _stage_end(trace_id, session.session_id, current_user.id, breakdown, "session_finish", risk_finish_started)
            _write_ai_log(
                db=db,
                trace_id=trace_id,
                session_id=session.session_id,
                user_id=current_user.id,
                full_context=full_context,
                reply_text=risk_reply_text,
                risk_flag=True,
                breakdown=breakdown,
            )
            yield _sse_event("done", {"status": "risk_blocked", "trace_id": trace_id})
            return

        await _raise_if_client_disconnected(is_disconnected)

        route_started = _stage_start(trace_id, session.session_id, current_user.id, "emotion_route")
        embedding_started = _stage_start(trace_id, session.session_id, current_user.id, "embedding")
        tags_started = _stage_start(trace_id, session.session_id, current_user.id, "suggested_tags")
        route_task = asyncio.create_task(ai_engine.classify_emotion_route(full_context, trace_id=trace_id))
        embedding_task = asyncio.create_task(ai_engine.get_embedding(full_context, trace_id=trace_id))
        tags_task = asyncio.create_task(ai_engine.generate_suggested_tags(full_context, trace_id=trace_id))
        yield _sse_event("asset_started", {"trace_id": trace_id})

        empathy_started = _stage_start(trace_id, session.session_id, current_user.id, "empathy_text")
        reply_chunks: List[str] = []
        async for delta in ai_engine.stream_empathy_text(full_context, trace_id=trace_id):
            await _raise_if_client_disconnected(is_disconnected)
            reply_chunks.append(delta)
            yield _sse_event("empathy_delta", {"delta": delta, "trace_id": trace_id})
        reply_text = "".join(reply_chunks).strip() or ai_engine._safe_fallback_reply()
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "empathy_text",
            empathy_started,
            reply_len=len(reply_text),
        )
        yield _sse_event("empathy_done", {"reply_text": reply_text, "trace_id": trace_id})

        await _raise_if_client_disconnected(is_disconnected)
        route_result, vector = await _await_route_and_embedding(
            route_task=route_task,
            embedding_task=embedding_task,
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            breakdown=breakdown,
            route_started=route_started,
            embedding_started=embedding_started,
        )
        route_task = None
        embedding_task = None
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "emotion_route",
            route_started,
            island_target=route_result["Island"],
            intensity=route_result["Intensity"],
        )
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "embedding",
            embedding_started,
            vector_size=len(vector),
        )

        await _raise_if_client_disconnected(is_disconnected)
        search_started = _stage_start(trace_id, session.session_id, current_user.id, "vector_search")
        candidate_images = search_engine.search_island_candidates(
            vector=vector,
            island_target=route_result["Island"],
            intensity=route_result["Intensity"],
            top_k=3,
        )
        _stage_end(
            trace_id,
            session.session_id,
            current_user.id,
            breakdown,
            "vector_search",
            search_started,
            candidate_count=len(candidate_images),
        )
        await _raise_if_client_disconnected(is_disconnected)
        poem_started = _stage_start(trace_id, session.session_id, current_user.id, "three_line_poem")
        candidate_images = await _hydrate_candidate_poems(
            full_context=full_context,
            candidate_images=candidate_images,
            trace_id=trace_id,
        )
        primary = candidate_images[0]
        generated_poem = primary["poem_content"]
        _stage_end(trace_id, session.session_id, current_user.id, breakdown, "three_line_poem", poem_started)
        recommended_tags = await _await_recommended_tags(
            tags_task=tags_task,
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            breakdown=breakdown,
            tags_started=tags_started,
        )
        tags_task = None

        await _raise_if_client_disconnected(is_disconnected)
        ticket_payload = {
            "image_url": primary.get("image_url"),
            "poem_content": generated_poem,
            "image_style": None,
            "user_diary_summary": full_context,
            "island_category": route_result["Island"],
            "selected_image_id": primary.get("image_id"),
        }
        ticket_started = _stage_start(trace_id, session.session_id, current_user.id, "ticket_create")
        new_ticket = crud.create_ticket(db, ticket_payload, user_id=current_user.id)
        _stage_end(trace_id, session.session_id, current_user.id, breakdown, "ticket_create", ticket_started, ticket_uid=new_ticket.ticket_uid)

        session_finish_started = _stage_start(trace_id, session.session_id, current_user.id, "session_finish")
        crud.update_chat_step(db, session.session_id, step=3)
        _stage_end(trace_id, session.session_id, current_user.id, breakdown, "session_finish", session_finish_started)

        _write_ai_log(
            db=db,
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            full_context=full_context,
            reply_text=reply_text,
            risk_flag=False,
            breakdown=breakdown,
        )

        ticket_data = {
            "id": new_ticket.id,
            "ticket_uid": new_ticket.ticket_uid,
            "image_url": primary.get("image_url"),
            "poem_content": generated_poem,
            "island_category": route_result["Island"],
            "is_public": False,
            "created_at": new_ticket.created_at,
            "recommended_tags": recommended_tags,
            "candidate_images": candidate_images,
        }
        yield _sse_event("asset_ready", {"ticket_data": ticket_data, "trace_id": trace_id})
        yield _sse_event(
            "done",
            {
                "status": "finished",
                "trace_id": trace_id,
                "elapsed_ms": int((time.perf_counter() - request_started) * 1000),
            },
        )
    except asyncio.CancelledError:
        await _cancel_background_tasks(route_task, embedding_task, tags_task)
        return
    except Exception as exc:
        await _cancel_background_tasks(route_task, embedding_task, tags_task)
        error_code = _map_generation_error(exc)
        _log_chat_event(
            logging.ERROR,
            "chat.reply.stream.failed",
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            error_code=error_code,
            error_type=type(exc).__name__,
            error_message=str(exc),
            elapsed_ms=int((time.perf_counter() - request_started) * 1000),
            breakdown=breakdown,
        )
        yield _sse_event("error", {"code": error_code, "message": str(exc), "trace_id": trace_id})
        yield _sse_event("done", {"status": "error", "trace_id": trace_id})


@router.post("/reply", response_model=schemas.ChatStepResponse)
async def reply_chat(
    reply_req: schemas.ChatReplyRequest,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    trace_id = uuid.uuid4().hex[:12]
    request_started = time.perf_counter()
    breakdown: Dict[str, int] = {}

    _log_chat_event(
        logging.INFO,
        "chat.reply.request.start",
        trace_id=trace_id,
        session_id=reply_req.session_id,
        user_id=current_user.id,
    )

    lookup_started = _stage_start(trace_id, reply_req.session_id, current_user.id, "session_lookup")
    session = crud.get_chat_session(db, reply_req.session_id)
    if not session:
        _stage_end(trace_id, reply_req.session_id, current_user.id, breakdown, "session_lookup", lookup_started, success=False, error_code="session_not_found")
        raise HTTPException(status_code=404, detail="Session not found")
    _stage_end(trace_id, reply_req.session_id, current_user.id, breakdown, "session_lookup", lookup_started, current_step=session.current_step)

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    if session.current_step not in {0, 1}:
        _log_chat_event(
            logging.INFO,
            "chat.reply.request.end",
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            state="finished",
            elapsed_ms=int((time.perf_counter() - request_started) * 1000),
            breakdown=breakdown,
        )
        return schemas.ChatStepResponse(session_id=session.session_id, state="finished", reply_text="本次会话已结束，请重新开始。")

    session, full_context = await _save_turn_1_and_build_context(
        db=db,
        session=session,
        reply_req=reply_req,
        trace_id=trace_id,
        user_id=current_user.id,
        breakdown=breakdown,
    )
    _assert_daily_ticket_limit_not_reached(db=db, user=current_user)

    try:
        return await _build_sync_final_response(
            db=db,
            session=session,
            current_user=current_user,
            full_context=full_context,
            trace_id=trace_id,
            breakdown=breakdown,
            request_started=request_started,
        )
    except HTTPException:
        raise
    except Exception as exc:
        if _is_mysql_unsupported_character_error(exc):
            raise HTTPException(status_code=400, detail="chat_contains_unsupported_characters") from exc
        error_code = _map_generation_error(exc)
        _log_chat_event(
            logging.ERROR,
            "chat.reply.request.failed",
            trace_id=trace_id,
            session_id=session.session_id,
            user_id=current_user.id,
            error_code=error_code,
            error_type=type(exc).__name__,
            error_message=str(exc),
            elapsed_ms=int((time.perf_counter() - request_started) * 1000),
            breakdown=breakdown,
            mode="compat_sync",
        )
        raise HTTPException(status_code=500, detail=_build_error_detail(error_code, trace_id))


@router.post("/reply/stream")
async def reply_chat_stream(
    reply_req: schemas.ChatReplyRequest,
    request: Request,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    trace_id = uuid.uuid4().hex[:12]
    request_started = time.perf_counter()
    breakdown: Dict[str, int] = {}

    lookup_started = _stage_start(trace_id, reply_req.session_id, current_user.id, "session_lookup")
    session = crud.get_chat_session(db, reply_req.session_id)
    if not session:
        _stage_end(trace_id, reply_req.session_id, current_user.id, breakdown, "session_lookup", lookup_started, success=False, error_code="session_not_found")
        raise HTTPException(status_code=404, detail="Session not found")
    _stage_end(trace_id, reply_req.session_id, current_user.id, breakdown, "session_lookup", lookup_started, current_step=session.current_step)

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    if session.current_step not in {0, 1}:
        raise HTTPException(status_code=409, detail="Stream reply only supports active sessions")

    session, full_context = await _save_turn_1_and_build_context(
        db=db,
        session=session,
        reply_req=reply_req,
        trace_id=trace_id,
        user_id=current_user.id,
        breakdown=breakdown,
    )
    _assert_daily_ticket_limit_not_reached(db=db, user=current_user)

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        _stream_final_reply_events(
            db=db,
            session=session,
            current_user=current_user,
            full_context=full_context,
            trace_id=trace_id,
            breakdown=breakdown,
            request_started=request_started,
            is_disconnected=request.is_disconnected,
        ),
        media_type="text/event-stream",
        headers=headers,
    )


@router.post("/confirm", response_model=schemas.BaseResponse)
def confirm_ticket(
    confirm_req: schemas.TicketConfirmRequest,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    ticket = crud.get_ticket_by_uid(db, confirm_req.ticket_uid)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if ticket.image_url != confirm_req.final_image_url:
        crud.update_ticket_selection(
            db,
            ticket_uid=ticket.ticket_uid,
            image_url=confirm_req.final_image_url,
            poem_content=confirm_req.final_poem_content,
            style=confirm_req.final_style,
            reroll_count=confirm_req.reroll_count,
            selected_image_id=confirm_req.final_image_url,
        )

    return schemas.BaseResponse(
        code=200,
        message="ticket_confirmed",
        data={
            "ticket_uid": ticket.ticket_uid,
            "final_image_url": confirm_req.final_image_url,
            "reroll_count": confirm_req.reroll_count,
        },
    )
