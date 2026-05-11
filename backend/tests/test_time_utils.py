from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app import schemas
from app.utils.time import serialize_utc_datetime, utc_now


def test_utc_now_does_not_depend_on_server_local_timezone():
    expected = datetime.now(timezone.utc).replace(tzinfo=None)

    assert abs((utc_now() - expected).total_seconds()) < 2


def test_serialize_utc_datetime_marks_naive_values_as_utc():
    assert serialize_utc_datetime(datetime(2026, 5, 11, 3, 18, 0)) == "2026-05-11T03:18:00Z"


def test_serialize_utc_datetime_converts_offset_values_to_utc():
    china_time = datetime(2026, 5, 11, 11, 18, 0, tzinfo=timezone(timedelta(hours=8)))

    assert serialize_utc_datetime(china_time) == "2026-05-11T03:18:00Z"


def test_ticket_schema_serializes_created_at_as_utc_marker():
    ticket = SimpleNamespace(
        id=1,
        ticket_uid="ticket-1",
        image_url="https://img/1.jpg",
        poem_content="poem",
        user_diary_summary="diary",
        island_category="RAIN",
        selected_tags=None,
        selected_image_id=None,
        hug_count=0,
        view_count=0,
        is_public=False,
        created_at=datetime(2026, 5, 11, 3, 18, 0),
    )

    data = schemas.TicketDTO.model_validate(ticket).model_dump(mode="json")

    assert data["created_at"] == "2026-05-11T03:18:00Z"
