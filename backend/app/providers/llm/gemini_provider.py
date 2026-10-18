"""Google Gemini LLM provider using the official google-genai SDK."""

from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Optional

from app.config import get_settings
from app.providers.llm.base import (
    LLMMessage,
    LLMProvider,
    LLMStreamEvent,
    LLMToolCall,
    LLMToolSpec,
)

logger = logging.getLogger(__name__)

ToolExecutor = Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]


class GeminiProvider(LLMProvider):
    """Gemini Flash backend with function calling and exponential backoff."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL or "gemini-3.8-flash"
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is not set. Add it to backend/.env to enable the assistant."
                )
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _tool_declarations(self, tools: List[LLMToolSpec]) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in tools
        ]

    def _thinking_config(self):
        """Keep thinking light so college-project chats stay snappy."""
        from google.genai import types

        model = (self.model or "").lower()
        # gemini-3.8-flash rejects MINIMAL; LOW is the lightest supported level.
        if model.startswith("gemini-3") or "flash-latest" in model:
            return types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW)
        return types.ThinkingConfig(thinking_budget=0)

    def _build_config(self, system_prompt: str, tools: List[LLMToolSpec]):
        from google.genai import types

        return types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[types.Tool(function_declarations=self._tool_declarations(tools))]
            if tools
            else None,
            temperature=0.3,
            thinking_config=self._thinking_config(),
        )

    def _history_to_contents(self, messages: List[LLMMessage]) -> List[Any]:
        """Map prior text turns only (no reconstructed function calls)."""
        from google.genai import types

        contents: List[Any] = []
        for msg in messages:
            if msg.role == "system":
                continue
            if msg.role == "user" and msg.content:
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=msg.content)],
                    )
                )
            elif msg.role == "assistant" and msg.content:
                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=msg.content)],
                    )
                )
            # Skip tool / bare tool-call assistant stubs from session history
        return contents

    def _is_transient(self, exc: Exception) -> bool:
        text = str(exc).lower()
        return any(
            token in text
            for token in (
                "429",
                "503",
                "unavailable",
                "high demand",
                "resource_exhausted",
                "rate limit",
                "quota",
                "too many requests",
                "deadline",
                "timed out",
                "timeout",
            )
        )

    def _friendly_error(self, exc: Exception) -> str:
        text = str(exc).lower()
        if "503" in text or "high demand" in text or "unavailable" in text:
            return (
                "Gemini is busy right now (high demand). "
                "Wait 20–30 seconds and try again — spikes are usually temporary."
            )
        if "429" in text or "rate limit" in text or "quota" in text:
            return "Gemini free-tier rate limit hit. Wait about a minute and try again."
        if "timed out" in text or "took too long" in text:
            return "The assistant timed out. Try a shorter question in a few seconds."
        return str(exc)

    def _model_candidates(self) -> List[str]:
        """Primary model plus lighter fallbacks when Google returns 503."""
        primary = self.model or "gemini-3.8-flash"
        fallbacks = [
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
        ]
        ordered: List[str] = []
        for m in [primary, *fallbacks]:
            if m and m not in ordered:
                ordered.append(m)
        return ordered

    async def _with_backoff(self, coro_factory, max_retries: int = 2, timeout: float = 25.0):
        delay = 1.2
        last_exc: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(coro_factory(), timeout=timeout)
            except asyncio.TimeoutError as e:
                last_exc = RuntimeError(
                    "Gemini took too long. Please try a shorter question."
                )
                logger.warning("Gemini call timed out (attempt %s)", attempt + 1)
                if attempt >= max_retries:
                    raise last_exc from e
            except Exception as e:
                last_exc = e
                if not self._is_transient(e) or attempt >= max_retries:
                    raise
                sleep_for = delay + random.uniform(0, 0.4)
                logger.warning(
                    "Gemini transient error (attempt %s/%s): %s; sleeping %.1fs",
                    attempt + 1,
                    max_retries + 1,
                    str(e)[:120],
                    sleep_for,
                )
                await asyncio.sleep(sleep_for)
                delay = min(delay * 2, 5.0)
        raise last_exc or RuntimeError("Gemini request failed")

    async def run_tool_loop(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        tools: List[LLMToolSpec],
        execute_tool: ToolExecutor,
        max_rounds: int = 3,
    ) -> AsyncIterator[LLMStreamEvent]:
        """
        Multi-turn tool calling that keeps Gemini's original Content objects
        (including thought_signature) — never rebuild functionCall parts.
        Hard overall deadline so the UI never spins for minutes.
        """
        from google.genai import types

        client = self._get_client()
        config = self._build_config(system_prompt, tools)
        contents = self._history_to_contents(messages)
        deadline = asyncio.get_event_loop().time() + 75.0
        models = self._model_candidates()
        active_model = models[0]

        for round_idx in range(max_rounds + 1):
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                yield LLMStreamEvent(
                    type="error",
                    error="The assistant timed out. Please try again in a moment.",
                )
                yield LLMStreamEvent(type="done")
                return

            response = None
            last_err: Optional[Exception] = None
            for model_name in models:
                active_model = model_name

                async def _call(m=model_name, contents=contents, config=config):
                    return await client.aio.models.generate_content(
                        model=m,
                        contents=contents,
                        config=config,
                    )

                try:
                    per_call = min(25.0, max(8.0, remaining - 5.0))
                    response = await self._with_backoff(
                        _call, max_retries=1, timeout=per_call
                    )
                    if model_name != models[0]:
                        logger.info("Fell back to Gemini model %s", model_name)
                    break
                except Exception as e:
                    last_err = e
                    if self._is_transient(e):
                        yield LLMStreamEvent(
                            type="status",
                            text="Gemini busy — trying another model…",
                        )
                        continue
                    break

            if response is None:
                yield LLMStreamEvent(
                    type="error",
                    error=self._friendly_error(
                        last_err or RuntimeError("Gemini unavailable")
                    ),
                )
                yield LLMStreamEvent(type="done")
                return

            model_content = None
            try:
                if response.candidates:
                    model_content = response.candidates[0].content
            except Exception:
                model_content = None

            tool_calls = self._extract_tool_calls(response)
            if tool_calls and model_content is not None:
                contents.append(model_content)

                fr_parts = []
                for tc in tool_calls:
                    yield LLMStreamEvent(
                        type="status",
                        text=f"Fetching {tc.name.replace('_', ' ')}…",
                    )
                    try:
                        result = await asyncio.wait_for(
                            execute_tool(tc.name, tc.arguments or {}),
                            timeout=20.0,
                        )
                    except asyncio.TimeoutError:
                        result = {
                            "ok": False,
                            "error": f"Tool {tc.name} timed out after 20s",
                        }
                    except Exception as e:
                        logger.exception("Tool %s failed", tc.name)
                        result = {"ok": False, "error": str(e)}
                    yield LLMStreamEvent(
                        type="tool_result",
                        tool_calls=[tc],
                        text=json.dumps({"name": tc.name, "result": result}, default=str),
                    )
                    fr_parts.append(
                        types.Part.from_function_response(
                            name=tc.name,
                            response={"result": result},
                        )
                    )
                contents.append(types.Content(role="user", parts=fr_parts))
                continue

            text = self._extract_text(response)
            if text:
                chunk_size = 48
                for i in range(0, len(text), chunk_size):
                    yield LLMStreamEvent(type="text", text=text[i : i + chunk_size])
                    await asyncio.sleep(0.005)
            elif tool_calls and model_content is None:
                yield LLMStreamEvent(
                    type="error",
                    error="Model returned tool calls without content; try again.",
                )
            yield LLMStreamEvent(type="done")
            return

        yield LLMStreamEvent(
            type="error",
            error="Too many tool rounds. Please ask a simpler question.",
        )
        yield LLMStreamEvent(type="done")

    async def stream_with_tools(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        tools: List[LLMToolSpec],
    ) -> AsyncIterator[LLMStreamEvent]:
        """Single-shot generate (no internal tool execution). Prefer run_tool_loop."""
        from google.genai import types

        client = self._get_client()
        config = self._build_config(system_prompt, tools)
        contents = self._history_to_contents(messages)

        async def _call():
            return await client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

        try:
            response = await self._with_backoff(_call, max_retries=1, timeout=25.0)
        except Exception as e:
            yield LLMStreamEvent(type="error", error=self._friendly_error(e))
            yield LLMStreamEvent(type="done")
            return

        model_content = None
        try:
            if response.candidates:
                model_content = response.candidates[0].content
        except Exception:
            model_content = None

        tool_calls = self._extract_tool_calls(response)
        if tool_calls:
            yield LLMStreamEvent(
                type="tool_calls",
                tool_calls=tool_calls,
                provider_content=model_content,
            )
            yield LLMStreamEvent(type="done")
            return

        text = self._extract_text(response)
        if text:
            chunk_size = 48
            for i in range(0, len(text), chunk_size):
                yield LLMStreamEvent(type="text", text=text[i : i + chunk_size])
                await asyncio.sleep(0.005)

        yield LLMStreamEvent(type="done")

    async def complete_with_tools(
        self,
        system_prompt: str,
        messages: List[LLMMessage],
        tools: List[LLMToolSpec],
        max_retries: int = 4,
    ) -> AsyncIterator[LLMStreamEvent]:
        async for event in self.stream_with_tools(system_prompt, messages, tools):
            yield event

    @staticmethod
    def _extract_text(response: Any) -> str:
        try:
            return (response.text or "").strip()
        except Exception:
            parts = []
            try:
                for cand in response.candidates or []:
                    content = getattr(cand, "content", None)
                    for part in getattr(content, "parts", None) or []:
                        if getattr(part, "thought", None):
                            continue
                        t = getattr(part, "text", None)
                        if t:
                            parts.append(t)
            except Exception:
                pass
            return "".join(parts).strip()

    @staticmethod
    def _extract_tool_calls(response: Any) -> List[LLMToolCall]:
        calls: List[LLMToolCall] = []
        try:
            for cand in response.candidates or []:
                content = getattr(cand, "content", None)
                for idx, part in enumerate(getattr(content, "parts", None) or []):
                    fc = getattr(part, "function_call", None)
                    if not fc:
                        continue
                    name = getattr(fc, "name", None) or ""
                    raw_args = getattr(fc, "args", None) or {}
                    if hasattr(raw_args, "items"):
                        args = dict(raw_args)
                    elif isinstance(raw_args, dict):
                        args = raw_args
                    else:
                        args = {}
                    sig = getattr(part, "thought_signature", None)
                    calls.append(
                        LLMToolCall(
                            id=f"{name}_{idx}",
                            name=name,
                            arguments=args,
                            thought_signature=sig,
                        )
                    )
        except Exception as e:
            logger.debug("Failed to extract tool calls: %s", e)
        return calls
