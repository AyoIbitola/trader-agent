import asyncio
from fastapi import FastAPI
from backend.router import router
from backend.telegram_bot import main

app = FastAPI()
app.include_router(router)

@app.on_event("startup")
async def startup():
    asyncio.create_task(main())

@app.get("/")
async def home():
    return {"message": "welcome"}