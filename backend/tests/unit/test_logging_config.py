import logging

from app.core.logging_config import RingBufferHandler, get_recent_logs


def test_ring_buffer_handler_captures_emitted_records():
    logger = logging.getLogger("test.ring_buffer")
    logger.setLevel(logging.INFO)
    handler = RingBufferHandler()
    logger.addHandler(handler)
    try:
        logger.info("something.happened key=%s", "value")
        entries = get_recent_logs(limit=5)
        assert any(e["message"] == "something.happened key=value" for e in entries)
        assert any(e["logger"] == "test.ring_buffer" for e in entries)
    finally:
        logger.removeHandler(handler)


def test_get_recent_logs_filters_by_level():
    logger = logging.getLogger("test.ring_buffer_levels")
    logger.setLevel(logging.INFO)
    handler = RingBufferHandler()
    logger.addHandler(handler)
    try:
        logger.info("info.marker.unique")
        logger.warning("warning.marker.unique")
        warnings_only = get_recent_logs(limit=50, level="WARNING")
        messages = [e["message"] for e in warnings_only]
        assert "warning.marker.unique" in messages
        assert "info.marker.unique" not in messages
    finally:
        logger.removeHandler(handler)
