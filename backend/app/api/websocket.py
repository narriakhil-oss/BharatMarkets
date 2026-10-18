"""WebSocket price streaming skeleton for real-time ticker updates."""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.redis_client import cache_get, get_redis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/prices")
async def websocket_prices(
    websocket: WebSocket,
    symbols: Optional[str] = Query(
        None,
        description="Comma-separated list of symbols to stream (e.g. RELIANCE.NS,TCS.NS)",
    ),
):
    """
    WebSocket endpoint streaming periodic price updates for subscribed stock symbols.

    Accepts comma-separated symbols query parameter. Emits JSON price payloads every 3 seconds.
    """
    await websocket.accept()
    symbol_list: List[str] = []
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    logger.info("WebSocket client connected. Subscribed symbols: %s", symbol_list)

    try:
        while True:
            # Check for incoming client messages without blocking indefinitely
            try:
                # Wait for any client ping/message for up to 3 seconds
                client_msg = await asyncio.wait_for(websocket.receive_text(), timeout=3.0)
                try:
                    payload = json.loads(client_msg)
                    if payload.get("action") == "subscribe" and "symbols" in payload:
                        new_symbols = payload.get("symbols", [])
                        symbol_list = [s.strip().upper() for s in new_symbols if s.strip()]
                        logger.info("Client updated subscription: %s", symbol_list)
                except Exception:
                    pass
            except asyncio.TimeoutError:
                pass  # Normal heartbeat tick timeout

            # Fetch cached quotes for subscribed symbols
            updates = []
            for sym in symbol_list:
                cached = await cache_get(f"stock:quote:{sym}")
                if cached:
                    updates.append(cached)
                else:
                    # Generic placeholder if not in cache
                    updates.append({
                        "symbol": sym,
                        "status": "waiting_for_tick",
                    })

            await websocket.send_json({
                "type": "PRICE_UPDATE",
                "count": len(updates),
                "data": updates,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally.")
    except Exception as e:
        logger.warning("WebSocket connection terminated: %s", e)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
