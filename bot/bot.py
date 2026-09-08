import os
from datetime import date

import httpx
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
TELEGRAM_BOT_API_KEY = os.getenv("TELEGRAM_BOT_API_KEY")
WEBAPP_URL = os.getenv("WEBAPP_URL")
API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")
AUTH_HEADERS = {"Authorization": f"Bearer {API_AUTH_TOKEN}"}

CHOOSING_CATEGORY, ENTERING_VALUE = range(2)

# Balance.value is a Postgres `integer` column (32-bit signed).
PG_INTEGER_MAX = 2_147_483_647


async def start(update: Update, context):
    if not WEBAPP_URL:
        await update.message.reply_text("WEBAPP_URL is not configured.")
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "Открыть приложение",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Кликай! Или используй /add чтобы добавить баланс и /balance чтобы посмотреть баланс за сегодня.",
        reply_markup=reply_markup,
    )


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/categories/", headers=AUTH_HEADERS)

    if response.status_code != 200:
        await update.message.reply_text("Не получилось загрузить категории, попробуй позже.")
        return ConversationHandler.END

    categories = response.json()
    if not categories:
        await update.message.reply_text("Категорий пока нет — сначала добавь хотя бы одну в веб-версии.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(f"{c['name']} ({c['currency']})", callback_data=str(c['id']))]
        for c in categories
    ]
    await update.message.reply_text("Выбери категорию:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_CATEGORY


async def category_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['cat_id'] = int(query.data)
    await query.edit_message_text("Введи сумму:")
    return ENTERING_VALUE


async def value_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        value = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Нужно целое число. Попробуй ещё раз:")
        return ENTERING_VALUE

    if not (-PG_INTEGER_MAX - 1 <= value <= PG_INTEGER_MAX):
        await update.message.reply_text("Слишком большое число. Попробуй ещё раз:")
        return ENTERING_VALUE

    cat_id = context.user_data['cat_id']
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/balance/",
            json=[{"cat_id": cat_id, "value": value}],
            headers=AUTH_HEADERS,
        )

    if response.status_code != 200:
        await update.message.reply_text(f"Ошибка: {response.text}")
        return ConversationHandler.END

    results = response.json()
    if results:
        entry = results[0]
        await update.message.reply_text(
            f"Добавлено: {entry['category_name']} — {entry['value']} "
            f"({entry['converted_value']:.2f} EUR)"
        )
        return ConversationHandler.END

    # Already has a record for today — update it instead of just reporting a no-op
    async with httpx.AsyncClient() as client:
        patch_response = await client.patch(
            f"{API_BASE_URL}/balance/",
            json={"cat_id": cat_id, "value": value},
            headers=AUTH_HEADERS,
        )

    if patch_response.status_code != 200:
        await update.message.reply_text(f"Ошибка: {patch_response.text}")
        return ConversationHandler.END

    balance = patch_response.json()["balance"]
    await update.message.reply_text(
        f"За сегодня уже была запись — обновила значение на {balance['value']}."
    )
    return ConversationHandler.END


async def add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


async def today_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today().isoformat()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/balances/",
            params={"from_date": today, "to_date": today},
            headers=AUTH_HEADERS,
        )

    if response.status_code != 200:
        await update.message.reply_text("Не получилось получить баланс, попробуй позже.")
        return

    balances = response.json()
    if not balances:
        await update.message.reply_text(
            "Записей за сегодня пока нет — самое время её добавить: /add"
        )
        return

    lines = [
        f"{item['category_name']}: {item['value']} ({item['converted_value']:.2f} EUR)"
        for item in balances
    ]
    total = sum(item['converted_value'] for item in balances)
    lines.append(f"\nИтого: {total:.2f} EUR")
    await update.message.reply_text("\n".join(lines))


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_API_KEY).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", today_balance))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            CHOOSING_CATEGORY: [CallbackQueryHandler(category_chosen)],
            ENTERING_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, value_entered)],
        },
        fallbacks=[CommandHandler("cancel", add_cancel)],
        allow_reentry=True,
        conversation_timeout=300,
    ))

    app.run_polling()

if __name__ == '__main__':
    main()
