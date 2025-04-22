import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from parser import parse_kaspi_product
from config import BOT_TOKEN, WEBHOOK_URL

# Обработчик команды "/start"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на товар Kaspi, и я покажу примерные продажи и спрос 📊")

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "kaspi.kz" not in url:
        await update.message.reply_text("Пожалуйста, отправь корректную ссылку на товар Kaspi.kz.")
        return

    # Парсинг данных с карточки товара Kaspi
    data = parse_kaspi_product(url)

    if not data:
        await update.message.reply_text("Не удалось спарсить данные с карточки 😢")
        return

    # Анализ продаж товара
    result = data.get("sales_analysis")
    if not result:
        await update.message.reply_text("Не удалось оценить продажи 😢")
        return

    # Формирование ответа
    response = (
        f"📦 *{data.get('title', 'Название товара не найдено')}*\n"
        f"🔢 ID товара: {data.get('product_id', 'неизвестно')}\n"
        f"💰 Цена: {data.get('price', 'неизвестно'):,} ₸\n"
        f"⭐ Всего оценок: {sum(data.get('ratings', {}).values())}\n"
        f"💬 Отзывов с текстом: {data.get('text_reviews', 0)}\n"
        f"📊 Рейтинг по звёздам:\n"
    )

    for rate in sorted(data.get('ratings', {}).keys(), reverse=True):
        response += f"  {rate}★ — {data['ratings'].get(rate)} шт.\n"

    response += (
        f"\n📅 Отзывы по датам:\n"
        f"  Сегодня: {data.get('reviews_today', 0)}\n"
        f"  За неделю: {data.get('reviews_week', 0)}\n"
        f"  За месяц: {data.get('reviews_month', 0)}\n\n"
    )

    month_revenue = result.get('avg_sales_month', 0) * data.get('price', 0)
    all_time_revenue = result.get('revenue_estimate', 0)

    response += (
        f"📦 Результат анализа продаж:\n"
        f"  ~ Продажи всего: {result.get('sales_estimate')} шт.\n"
        f"  ~ Выручка за всё время: {all_time_revenue:,.0f} ₸\n\n"

        f"📈 Примерные продажи:\n"
        f"  • В день: {result.get('avg_sales_today', 0)} шт. "
        f"({result.get('daily_range', [0, 0])[0]}–{result.get('daily_range', [0, 0])[1]} шт.)\n"
        f"  • За неделю: {result.get('avg_sales_week', 0)} шт. "
        f"({result.get('weekly_range', [0, 0])[0]}–{result.get('weekly_range', [0, 0])[1]} шт.)\n"
        f"  • За месяц: {result.get('avg_sales_month', 0)} шт. "
        f"({result.get('monthly_range', [0, 0])[0]}–{result.get('monthly_range', [0, 0])[1]} шт.)\n\n"

        f"💰 Выручка за месяц: {month_revenue:,.0f} ₸\n\n"

        f"📌 Статус активности: {result.get('status', '')}\n"
        f"🕒 Последний отзыв: {result.get('last_review_date', 'неизвестно')}\n"
        f"{result.get('confidence', '')}"
    ).replace(",", " ")

    # Отправка ответа пользователю
    await update.message.reply_text(response, parse_mode="Markdown")


# Фейковый веб-сервер для Render (обязательный хак)
class HelloHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Kaspi Parser Bot is running!')


# Запуск фейкового веб-сервера
def run_web_server():
    port = int(os.environ.get("PORT", 10000))  # Render ожидает переменную PORT
    server = HTTPServer(("", port), HelloHandler)
    server.serve_forever()


# Запуск веб-сервера в отдельном потоке
threading.Thread(target=run_web_server, daemon=True).start()


# Настройка Webhook
async def set_webhook():
    # Получаем URL для webhook
    webhook_url = WEBHOOK_URL + "/" + BOT_TOKEN
    await app.bot.set_webhook(webhook_url)


# Запуск Telegram-бота
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Устанавливаем webhook при старте
import asyncio
asyncio.run(set_webhook())

# Добавляем обработчики
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущен с Webhook ✅")
