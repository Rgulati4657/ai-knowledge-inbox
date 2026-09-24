from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: str
    level: str
    logger: str
    message: str


class LogListResponse(BaseModel):
    logs: list[LogEntry]
