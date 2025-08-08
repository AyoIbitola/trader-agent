import logging
import asyncio
import aiohttp
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FASTAPI_URL = os.getenv("FAST_API_URL", "http://127.0.0.1:8000")  

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_jobs = {}  

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Stop Predictions", callback_data="stop_predictions")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Forex Signal Bot 📈. Type /predict to get the latest signals.\n"
        "Or wait for automatic predictions every 15 minutes.",
        reply_markup=reply_markup,
    )
    await schedule_prediction_job(update.effective_chat.id, context)


async def predict_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_prediction(update.effective_chat.id, context)

async def send_prediction(chat_id, context):
    try:
        timeout = aiohttp.ClientTimeout(total=120)  
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{FASTAPI_URL}/predict") as response:
                if response.status == 200:
                    data = await response.json()
                    predictions = data.get("predictions", [])
                    message = "📊🤖Latest Forex Predictions:\n\n"

                    for pred in predictions:
                        pair = pred["pair"].replace("_", "/")
                        signal = pred["signal"]
                        price = pred["predicted_price"]
                        message += f"• 📈🚀{pair}: {signal.upper()} @ {price:.3f}\n"

                    keyboard = [
                        [InlineKeyboardButton("Stop Predictions", callback_data="stop_predictions")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
                else:
                    await context.bot.send_message(chat_id=chat_id, text="⚠️ Failed to fetch predictions from the server.")
    except Exception as e:
        logger.error(f"Error fetching predictions: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ Error occurred while getting predictions.")


async def prediction_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await send_prediction(chat_id, context)


async def schedule_prediction_job(chat_id, context):
    
    if chat_id in user_jobs:
        user_jobs[chat_id].schedule_removal()
    job = context.job_queue.run_repeating(
        prediction_job, interval=900, first=0, chat_id=chat_id  # Changed interval to 60 seconds (1 minute)
    )
    user_jobs[chat_id] = job


async def stop_predictions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    if chat_id in user_jobs:
        user_jobs[chat_id].schedule_removal()
        del user_jobs[chat_id]
        await query.edit_message_text("⏹️ Automatic predictions stopped. Use /start to resume.")
    else:
        await query.edit_message_text("No active prediction job found.")


async def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("predict", predict_handler))
    application.add_handler(CallbackQueryHandler(stop_predictions_callback, pattern="stop_predictions"))

    logger.info("Telegram bot started.")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
  
    await application.updater.idle()
    await application.stop()
    await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
