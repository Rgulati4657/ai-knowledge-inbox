import logging
import sys
from collections import deque
from datetime import datetime, timezone

_RING_BUFFER_SIZE = 500
_log_ring_buffer: deque[dict] = deque(maxlen=_RING_BUFFER_SIZE)


class RingBufferHandler(logging.Handler):
    """Keeps the last N log records in memory so the API/UI can read them
    without shipping to an external log aggregator. Deliberately not
    persisted to disk -- restart clears it, which is fine for a single-user
    take-home; see docs/ARCHITECTURE.md for the production alternative.
    """

    def emit(self, record: logging.LogRecord) -> None:
        _log_ring_buffer.append(
            {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
        )


def get_recent_logs(limit: int = 100, level: str | None = None) -> list[dict]:
    entries = list(_log_ring_buffer)[::-1]
    if level:
        entries = [e for e in entries if e["level"] == level.upper()]
    return entries[:limit]


def configure_logging() -> None:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )

    ring_handler = RingBufferHandler()
    ring_handler.setLevel(logging.INFO)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [stream_handler, ring_handler]

    # Quiet down noisy third-party loggers, keep our own at INFO.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
