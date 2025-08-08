from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.database.models import Prediction
from sqlalchemy import func

async def save_prediction(db: AsyncSession,pair: str,signal: str,predicted_price:float):
    new_prediction = Prediction(
        pair=pair,
        signal = signal,
        predicted_price = predicted_price
    )

    db.add(new_prediction)
    await db.commit()
    await db.refresh(new_prediction)



async def update_actual_price(db: AsyncSession, prediction_id: int , actual_price):
    result = await db.execute(select(Prediction).where(Prediction.id==prediction_id))
    prediction = result.scalars().first()
    if prediction:
        prediction.actual_price=actual_price
        await db.commit()
        await db.refresh(prediction)

    return prediction

async def get_prediction_history(db: AsyncSession,limit: int = 50):
    result = await db.execute(select(Prediction).order_by(Prediction.timestamp.desc()).limit(limit))
    return result.scalars().all()

async def calculate_accuracy(db: AsyncSession):
    result = await db.execute(
        select(Prediction).where(Prediction.actual_price != None)
    )
    predictions = result.scalars().all()

    if not predictions:
        return {"message": "No predictions with actual prices available."}

    correct = 0
    total = 0

    for p in predictions:
        predicted = p.predicted_price
        actual = p.actual_price

        if predicted is None or actual is None:
            continue

      
        if p.signal == "buy" and actual > predicted:
            correct += 1
        elif p.signal == "sell" and actual < predicted:
            correct += 1
        elif p.signal == "hold":
            
            if abs(actual - predicted) / predicted < 0.001:
                correct += 1

        total += 1

    accuracy = round((correct / total) * 100, 2) if total > 0 else 0.0

    return {
        "total_predictions": total,
        "correct_predictions": correct,
        "accuracy_percent": accuracy
    }
