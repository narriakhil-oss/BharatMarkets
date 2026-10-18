"""Database seed script populating exchanges, nifty 100 stocks, indices, snapshots, and fundamentals."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, Base, engine
from app.models.exchange import Exchange
from app.models.fundamental import Fundamental
from app.models.index_model import Index
from app.models.price import StockSnapshot
from app.models.stock import Stock
from app.providers.yfinance_provider import YFinanceProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("seed")


def find_stocks_file() -> Path:
    """Find the path to nifty_100_stocks.json."""
    candidates = [
        backend_dir.parent / "data" / "nifty_100_stocks.json",
        backend_dir / "data" / "nifty_100_stocks.json",
        Path.cwd() / "data" / "nifty_100_stocks.json",
        Path.cwd().parent / "data" / "nifty_100_stocks.json",
        Path("/app/data/nifty_100_stocks.json"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError("Could not find nifty_100_stocks.json file.")


async def init_tables() -> None:
    """Create all database tables if they do not exist."""
    logger.info("Verifying and creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tables created / verified.")


async def seed_exchanges(session: AsyncSession) -> Dict[str, Exchange]:
    """Ensure NSE and BSE exchanges exist in DB."""
    logger.info("Seeding Exchanges...")
    exchanges = {
        "NSE": {
            "code": "NSE",
            "name": "National Stock Exchange of India",
            "timezone": "Asia/Kolkata",
            "is_active": True,
        },
        "BSE": {
            "code": "BSE",
            "name": "BSE Limited (Bombay Stock Exchange)",
            "timezone": "Asia/Kolkata",
            "is_active": True,
        },
    }

    result_map: Dict[str, Exchange] = {}
    for code, data in exchanges.items():
        stmt = select(Exchange).filter(Exchange.code == code)
        res = await session.execute(stmt)
        obj = res.scalar_one_or_none()
        if not obj:
            obj = Exchange(**data)
            session.add(obj)
            await session.flush()
            logger.info("Created Exchange: %s", code)
        result_map[code] = obj

    await session.commit()
    return result_map


async def seed_indices(session: AsyncSession, exchange_map: Dict[str, Exchange], data: Dict[str, Any]) -> None:
    """Seed benchmark indices."""
    logger.info("Seeding Benchmark Indices...")
    indices_data = data.get("indices", {})

    for key, item in indices_data.items():
        symbol = item["symbol"]
        display_name = item["display_name"]
        ex_code = item.get("exchange", "NSE")
        exchange = exchange_map.get(ex_code, exchange_map["NSE"])

        stmt = select(Index).filter(Index.symbol == symbol)
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()

        if not existing:
            idx = Index(
                symbol=symbol,
                name=key.replace("_", " "),
                display_name=display_name,
                exchange_id=exchange.id,
            )
            session.add(idx)
            logger.info("Created Index: %s (%s)", display_name, symbol)

    await session.commit()


async def seed_stocks(session: AsyncSession, exchange_map: Dict[str, Exchange], data: Dict[str, Any]) -> List[Stock]:
    """Seed all 100 stocks."""
    logger.info("Seeding Stock records...")
    stock_list = data.get("stocks", [])
    nse = exchange_map["NSE"]
    stocks_seeded: List[Stock] = []

    for item in stock_list:
        symbol = item["symbol"]
        stmt = select(Stock).filter(Stock.symbol == symbol)
        res = await session.execute(stmt)
        stock = res.scalar_one_or_none()

        if not stock:
            stock = Stock(
                symbol=symbol,
                name=item["name"],
                exchange_id=nse.id,
                isin=item.get("isin"),
                sector=item.get("sector"),
                industry=item.get("industry"),
                lot_size=1,
                tick_size=Decimal("0.05"),
                circuit_limit_pct=20,
                is_active=True,
            )
            session.add(stock)
            await session.flush()
        stocks_seeded.append(stock)

    await session.commit()
    logger.info("Seeded %d stocks in database.", len(stocks_seeded))
    return stocks_seeded


async def fetch_and_populate_snapshots(
    session: AsyncSession,
    stocks: List[Stock],
    provider: YFinanceProvider,
) -> None:
    """Fetch quotes for all stocks and populate stock_snapshots table."""
    logger.info("Fetching initial real-time quotes via yfinance for %d stocks...", len(stocks))
    now_utc = datetime.now(timezone.utc)
    success_count = 0

    # Process in batches of 10 to balance speed and reliability
    batch_size = 10
    for i in range(0, len(stocks), batch_size):
        batch = stocks[i : i + batch_size]
        symbols = [s.symbol for s in batch]
        logger.info("Fetching quote batch %d to %d of %d...", i + 1, min(i + batch_size, len(stocks)), len(stocks))

        quotes = await provider.get_bulk_quotes(symbols)
        quote_map = {q["symbol"]: q for q in quotes if "symbol" in q}

        for stock in batch:
            q = quote_map.get(stock.symbol)
            if not q:
                continue

            snap_stmt = select(StockSnapshot).filter(StockSnapshot.stock_id == stock.id)
            snap_res = await session.execute(snap_stmt)
            snap = snap_res.scalar_one_or_none()

            if not snap:
                snap = StockSnapshot(
                    stock_id=stock.id,
                    ltp=q["ltp"],
                    prev_close=q["prev_close"],
                    change=q["change"],
                    change_pct=q["change_pct"],
                    day_high=q.get("day_high"),
                    day_low=q.get("day_low"),
                    high_52w=q.get("high_52w"),
                    low_52w=q.get("low_52w"),
                    volume=q.get("volume"),
                    updated_at=now_utc,
                )
                session.add(snap)
            else:
                snap.ltp = q["ltp"]
                snap.prev_close = q["prev_close"]
                snap.change = q["change"]
                snap.change_pct = q["change_pct"]
                snap.day_high = q.get("day_high")
                snap.day_low = q.get("day_low")
                snap.high_52w = q.get("high_52w")
                snap.low_52w = q.get("low_52w")
                snap.volume = q.get("volume")
                snap.updated_at = now_utc

            success_count += 1

        await session.commit()
        # Brief pause between batches
        await asyncio.sleep(0.5)

    logger.info("Successfully populated %d stock snapshots.", success_count)


async def fetch_and_populate_fundamentals(
    session: AsyncSession,
    stocks: List[Stock],
    provider: YFinanceProvider,
) -> None:
    """Fetch fundamentals for stocks and populate fundamentals table."""
    logger.info("Fetching fundamentals via yfinance...")
    now_utc = datetime.now(timezone.utc)
    success_count = 0

    # Process in batches of 10
    batch_size = 10
    for i in range(0, len(stocks), batch_size):
        batch = stocks[i : i + batch_size]
        logger.info("Fetching fundamentals batch %d to %d of %d...", i + 1, min(i + batch_size, len(stocks)), len(stocks))

        tasks = [provider.get_fundamentals(s.symbol) for s in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for stock, res in zip(batch, results):
            if isinstance(res, Exception) or not isinstance(res, dict):
                continue

            fund_stmt = select(Fundamental).filter(Fundamental.stock_id == stock.id)
            fund_res = await session.execute(fund_stmt)
            fund = fund_res.scalar_one_or_none()

            if not fund:
                fund = Fundamental(
                    stock_id=stock.id,
                    market_cap=res.get("market_cap"),
                    pe_ratio=res.get("pe_ratio"),
                    pb_ratio=res.get("pb_ratio"),
                    eps=res.get("eps"),
                    roe=res.get("roe"),
                    dividend_yield=res.get("dividend_yield"),
                    face_value=res.get("face_value"),
                    book_value=res.get("book_value"),
                    updated_at=now_utc,
                )
                session.add(fund)
            else:
                fund.market_cap = res.get("market_cap")
                fund.pe_ratio = res.get("pe_ratio")
                fund.pb_ratio = res.get("pb_ratio")
                fund.eps = res.get("eps")
                fund.roe = res.get("roe")
                fund.dividend_yield = res.get("dividend_yield")
                fund.book_value = res.get("book_value")
                fund.updated_at = now_utc

            success_count += 1

        await session.commit()
        await asyncio.sleep(0.5)

    logger.info("Successfully populated %d company fundamental records.", success_count)


async def main() -> None:
    """Run full database seeding sequence."""
    logger.info("Starting BharatMarkets Database Seeding...")

    # 1. Initialize tables
    await init_tables()

    # 2. Load seed file
    stocks_file = find_stocks_file()
    with open(stocks_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    provider = YFinanceProvider()

    async with AsyncSessionLocal() as session:
        # 3. Seed exchanges
        exchange_map = await seed_exchanges(session)

        # 4. Seed indices
        await seed_indices(session, exchange_map, data)

        # 5. Seed stock entities
        stocks = await seed_stocks(session, exchange_map, data)

        # 6. Fetch quotes and populate snapshots
        await fetch_and_populate_snapshots(session, stocks, provider)

        # 7. Fetch fundamentals
        await fetch_and_populate_fundamentals(session, stocks, provider)

    logger.info("Database seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
