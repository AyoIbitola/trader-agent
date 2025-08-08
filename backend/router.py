from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import get_db
from backend.crud import (
    save_prediction,
    get_prediction_history,
    calculate_accuracy,
    update_actual_price
)
from utils.data_fetcher import fetch_pair
from ai_core.live_predict import predict
import asyncio
router = APIRouter()

pairs = ["XAU_USD", "EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD"]


@router.get("/predict")
async def run_prediction(db: AsyncSession = Depends(get_db)):
    results = []
    
    for pair in pairs:
        try:
            fetch_pair(pair)
            result = predict(pair)  
 
            await save_prediction(
                db=db,
                pair=pair,
                signal=result["signal"],
                
                predicted_price=result["price"]
            )

            results.append({
                "pair": pair,
                "signal": result["signal"],
                "predicted_price": result["price"]
            })

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediction failed for {pair}: {str(e)}")

    return {"predictions": results}



@router.get("/history")
async def get_history(limit: int = 50, db: AsyncSession = Depends(get_db)):
    predictions = await get_prediction_history(db, limit)
    return {"history": [p.as_dict() for p in predictions]}  





@router.get("/accuracy")
async def update_and_calculate_accuracy(db: AsyncSession = Depends(get_db)):
    predictions = await get_prediction_history(db, limit=50)

  
    predictions_data = [ {"id": p.id, "pair": p.pair} for p in predictions ]

    for p in predictions_data:
        try:
            df = await asyncio.to_thread(fetch_pair, p["pair"])
            if df.empty:
                raise ValueError(f"No data for {p['pair']}")
            actual_price = df.iloc[-1]["close"]
            await update_actual_price(db, p["id"], actual_price)
        except Exception as e:
            print(f"❌ Error reading CSV or updating price for {p['pair']}: {e}")

    return await calculate_accuracy(db)