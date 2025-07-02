import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Update
from telegram.ext import ApplicationBuilder, CommandHandler


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
TELEGRAM_BOT_API_KEY = os.getenv("TELEGRAM_BOT_API_KEY")


async def start(update: Update, context):
    keyboard = [
        [
            InlineKeyboardButton(
                "Открыть приложение",
                web_app=WebAppInfo(url="https://d0f8-178-220-71-202.ngrok-free.app")
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Кликай!", reply_markup=reply_markup
    )


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_API_KEY).build()

    app.add_handler(CommandHandler("start", start))

    app.run_polling()

if __name__ == '__main__':
    main()

