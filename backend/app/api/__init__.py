"""API package for BharatMarkets."""

from app.api.websocket import router as ws_router

__all__ = ["ws_router"]
