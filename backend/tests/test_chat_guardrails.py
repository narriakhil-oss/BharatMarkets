"""Chat system-prompt / session / tool-failure guardrail tests."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.providers.llm.base import LLMProvider, LLMStreamEvent, LLMToolCall
from app.services.chat_service import (
    SYSTEM_PROMPT,
    ChatService,
    ChatSessionStore,
    MAX_SESSION_MESSAGES,
)


def test_system_prompt_requires_tools_only_numbers():
    assert "ONLY use numbers" in SYSTEM_PROMPT or "Never invent" in SYSTEM_PROMPT
    assert "Not financial advice" in SYSTEM_PROMPT
    assert "guarantees" in SYSTEM_PROMPT.lower() or "guarantee" in SYSTEM_PROMPT.lower()


def test_session_store_keeps_last_10():
    store = ChatSessionStore(max_messages=MAX_SESSION_MESSAGES)
    sid = "test-session"
    for i in range(15):
        store.append(sid, "user" if i % 2 == 0 else "assistant", f"msg-{i}")
    msgs = store.get(sid)
    assert len(msgs) == 10
    assert msgs[0].content == "msg-5"
    assert msgs[-1].content == "msg-14"


class FakeLLM(LLMProvider):
    """LLM that requests get_history then answers with tool numbers only."""

    def __init__(self):
        self.calls = 0

    async def stream_with_tools(self, system_prompt, messages, tools):
        self.calls += 1
        if self.calls == 1:
            yield LLMStreamEvent(
                type="tool_calls",
                tool_calls=[
                    LLMToolCall(
                        id="1",
                        name="get_history",
                        arguments={"symbol": "RELIANCE", "period": "3M"},
                    )
                ],
            )
            yield LLMStreamEvent(type="done")
            return
        yield LLMStreamEvent(
            type="text",
            text="RELIANCE moved from tool data only. Model-generated signal for a college project. Not financial advice.",
        )
        yield LLMStreamEvent(type="done")

    async def complete_with_tools(self, system_prompt, messages, tools, max_retries=4):
        async for event in self.stream_with_tools(system_prompt, messages, tools):
            yield event


@pytest.mark.asyncio
async def test_chat_reports_tool_failure_without_inventing():
    class FailHistoryLLM(LLMProvider):
        def __init__(self):
            self.round = 0

        async def stream_with_tools(self, system_prompt, messages, tools):
            self.round += 1
            if self.round == 1:
                yield LLMStreamEvent(
                    type="tool_calls",
                    tool_calls=[
                        LLMToolCall(
                            id="1", name="get_history", arguments={"symbol": "NOPE"}
                        )
                    ],
                )
                yield LLMStreamEvent(type="done")
                return
            tool_msgs = [m for m in messages if m.role == "tool"]
            assert tool_msgs, "Tool result must be fed back to the model"
            payload = json.loads(tool_msgs[-1].content)
            assert payload.get("ok") is False
            yield LLMStreamEvent(
                type="text",
                text="I could not load history for that symbol — the data tool failed.",
            )
            yield LLMStreamEvent(type="done")

        async def complete_with_tools(self, system_prompt, messages, tools, max_retries=4):
            async for event in self.stream_with_tools(system_prompt, messages, tools):
                yield event

    provider = MagicMock()
    market = MagicMock()
    history = MagicMock()
    history.get_history = AsyncMock(side_effect=ValueError("Could not resolve"))

    svc = ChatService(provider=provider, market_service=market, llm=FailHistoryLLM())
    svc.history_service = history

    events = []
    async for ev in svc.stream_chat("Summarize NOPE last 3 months", session_id="guard-1"):
        events.append(ev)

    texts = "".join(e.get("content", "") for e in events if e.get("type") == "text")
    assert "failed" in texts.lower() or "could not" in texts.lower()
    assert "InventedPrice" not in texts


@pytest.mark.asyncio
async def test_chat_happy_path_streams_text():
    provider = MagicMock()
    market = MagicMock()
    svc = ChatService(provider=provider, market_service=market, llm=FakeLLM())

    from app.schemas.chat import HistorySummary, PricePoint
    from decimal import Decimal

    svc.history_service.get_history = AsyncMock(
        return_value=HistorySummary(
            symbol="RELIANCE.NS",
            name="Reliance",
            period="3M",
            start_price=Decimal("100"),
            end_price=Decimal("110"),
            change_pct=Decimal("10"),
            high=Decimal("115"),
            low=Decimal("95"),
            series=[PricePoint(date="2024-01-01", close=Decimal("100"))],
        )
    )

    events = []
    async for ev in svc.stream_chat("Summarize RELIANCE's last 3 months", session_id="ok-1"):
        events.append(ev)

    types = [e["type"] for e in events]
    assert "session" in types
    assert "text" in types
    assert "structured" in types
    assert types[-1] == "done"
    structured = next(e for e in events if e["type"] == "structured")
    assert structured["data"]["history"]["symbol"] == "RELIANCE.NS"
