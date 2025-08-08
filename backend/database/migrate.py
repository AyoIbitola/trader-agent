import asyncio
from database.db import engine, Base
from database.models import Prediction,Accuracy

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created")

if __name__ == "__main__":
    asyncio.run(init_models())

