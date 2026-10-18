"""Abstract LLM provider interface for swappable chat backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional


@dataclass
class LLMMessage:
    role: str  # user | assistant | system | tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List["LLMToolCall"]] = None
    # Opaque provider payload (e.g. Gemini Content) — echo back for tool rounds
    provider_content: Any = None


@dataclass
class LLMToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]
    thought_signature: Optional[bytes] = None


@dataclass
class LLMToolSpec:
    name: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class LLMStreamEvent:
    """Normalized stream events from any LLM backend."""

    type: str  # text | tool_calls | tool_result | status | error | done
    text: str = ""
    tool_calls: List[LLMToolCall] = field(default_factory=list)
    error: str = ""
    # Raw model Content to replay on the next generate_content turn
    provider_content: Any = None


class LLMProvider(ABC):
    """Interface so Gemini can be swapped for another model later."""

    @abstractmethod
    async def stream_with_tools(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        tools: List[LLMToolSpec],
    ) -> AsyncIterator[LLMStreamEvent]:
        """
        Stream a completion that may request tool calls.

        Implementations should yield:
          - type=tool_calls when the model wants tools (then stop the turn)
          - type=text for streamed assistant tokens
          - type=error on failures
          - type=done when finished
        """
        ...
        yield LLMStreamEvent(type="done")  # pragma: no cover

    async def run_tool_loop(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        tools: List[LLMToolSpec],
        execute_tool,
        max_rounds: int = 4,
    ) -> AsyncIterator[LLMStreamEvent]:
        """
        Default multi-turn tool loop (for mocks / non-Gemini providers).
        GeminiProvider overrides this to preserve thought_signature.
        """
        import json

        working = list(messages)
        for _ in range(max_rounds + 1):
            tool_calls: List[LLMToolCall] = []
            async for event in self.stream_with_tools(system_prompt, working, tools):
                if event.type == "error":
                    yield event
                    yield LLMStreamEvent(type="done")
                    return
                if event.type == "tool_calls":
                    tool_calls = event.tool_calls
                elif event.type == "text":
                    yield event
                elif event.type == "done":
                    pass

            if not tool_calls:
                yield LLMStreamEvent(type="done")
                return

            working.append(
                LLMMessage(role="assistant", content="", tool_calls=tool_calls)
            )
            for tc in tool_calls:
                yield LLMStreamEvent(
                    type="status",
                    text=f"Fetching {tc.name.replace('_', ' ')}…",
                )
                result = await execute_tool(tc.name, tc.arguments or {})
                yield LLMStreamEvent(
                    type="tool_result",
                    tool_calls=[tc],
                    text=json.dumps({"name": tc.name, "result": result}, default=str),
                )
                working.append(
                    LLMMessage(
                        role="tool",
                        name=tc.name,
                        tool_call_id=tc.id,
                        content=json.dumps(result, default=str),
                    )
                )

        yield LLMStreamEvent(
            type="error",
            error="Too many tool rounds. Please ask a simpler question.",
        )
        yield LLMStreamEvent(type="done")

    @abstractmethod
    async def complete_with_tools(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        tools: List[LLMToolSpec],
        max_retries: int = 4,
    ) -> AsyncIterator[LLMStreamEvent]:
        """Higher-level helper with retries; may be implemented by subclasses."""
        ...
        yield LLMStreamEvent(type="done")  # pragma: no cover
