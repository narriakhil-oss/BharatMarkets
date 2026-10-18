"""Streaming chat assistant endpoint."""

from __future__ import annotations

import json
import logging
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.rate_limit import limiter
from app.core.redis_client import DecimalDateEncoder
from app.dependencies import get_chat_service
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatHealthResponse(BaseModel):
    status: str
    gemini_configured: bool
    model: str


@router.get(
    "/health",
    response_model=ChatHealthResponse,
    summary="Chat subsystem health",
)
async def chat_health(
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatHealthResponse:
    from app.config import get_settings

    settings = get_settings()
    return ChatHealthResponse(
        status="ok",
        gemini_configured=bool(settings.GEMINI_API_KEY),
        model=settings.GEMINI_MODEL,
    )


@router.post(
    "",
    summary="AI chat (SSE stream)",
    description=(
        "Stream an assistant reply with optional tool-backed structured data "
        "(history series, forecast, signal) for charts. Rate limit: 20/minute per IP."
    ),
)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> StreamingResponse:
    """POST /api/v1/chat — Server-Sent Events stream."""

    async def event_generator() -> AsyncIterator[str]:
        async for event in chat_service.stream_chat(
            message=body.message,
            session_id=body.session_id,
            client_history=body.history,
        ):
            payload = json.dumps(event, cls=DecimalDateEncoder)
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
