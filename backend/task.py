#wanted to use this for the apschceduler but I'll just leave it incase
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.db import async_session
from backend.database.models import Prediction
from datetime import datetime, timedelta, timezone
from utils.data_fetcher import fetch_pair

async def upddate_actual_prices():
    async with async_session as session:
        for pair   in ["XAU_USD", "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]:
            price = fetch_pair(pair)

            two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
            result = await session.execute(
                 select(Prediction)
                .where(Prediction.pair == pair)
                .where(Prediction.actual_price.is_(None))
                .where(Prediction.timestamp >= two_hours_ago)
            )
            predictions = result.scalars().all()

            for pred in predictions:
                pred.actual_price = price

            await session.commit()


