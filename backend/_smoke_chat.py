import asyncio
import json

from app.providers.llm.base import LLMMessage, LLMToolSpec
from app.providers.llm.gemini_provider import GeminiProvider


async def main() -> None:
    llm = GeminiProvider()
    print("model", llm.model)
    tools = [
        LLMToolSpec(
            name="get_market_overview",
            description="Today market snapshot",
            parameters={
                "type": "object",
                "properties": {"limit": {"type": "integer"}},
            },
        )
    ]
    msgs = [LLMMessage(role="user", content="How is the market today? Use the tool.")]
    tool_calls = []
    provider_content = None
    async for ev in llm.stream_with_tools("You must call get_market_overview.", msgs, tools):
        print("ev1", ev.type, (ev.error or "")[:80], "n_tc", len(ev.tool_calls))
        if ev.type == "tool_calls":
            tool_calls = ev.tool_calls
            provider_content = ev.provider_content
            for tc in tool_calls:
                print("  tc", tc.name, "sig", bool(tc.thought_signature))
    if not tool_calls:
        print("NO TOOL CALLS")
        return
    msgs.append(
        LLMMessage(
            role="assistant",
            content="",
            tool_calls=tool_calls,
            provider_content=provider_content,
        )
    )
    payload = json.dumps(
        {"ok": True, "data": {"status": "OPEN", "indices": [], "gainers": [], "losers": []}}
    )
    msgs.append(LLMMessage(role="tool", name=tool_calls[0].name, content=payload))
    async for ev in llm.stream_with_tools(
        "Summarize the tool result in one short sentence.", msgs, tools
    ):
        print("ev2", ev.type, (ev.text or ev.error or "")[:200])


if __name__ == "__main__":
    asyncio.run(main())
