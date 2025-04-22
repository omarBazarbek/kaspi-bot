from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from parser import parse_kaspi_product
from config import BOT_TOKEN
import os

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на товар Kaspi, и я покажу примерные продажи и спрос 📊")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "kaspi.kz" not in url:
        await update.message.reply_text("Пожалуйста, отправь корректную ссылку на товар Kaspi.kz.")
        return

    # Парсим данные товара с анализом
    data = parse_kaspi_product(url)

    if not data:
        await update.message.reply_text("Не удалось спарсить данные с карточки 😢")
        return

    result = data.get("sales_analysis")
    if not result:
        await update.message.reply_text("Не удалось оценить продажи 😢")
        return

    # Сборка ответа
    response = (
        f"📦 *{data.get('title', 'Название товара не найдено')}*\n"
        f"🔢 ID товара: {data.get('product_id', 'неизвестно')}\n"
        f"💰 Цена: {data.get('price', 'неизвестно'):,} ₸\n"
        f"⭐ Всего оценок: {sum(data.get('ratings', {}).values())}\n"
        f"💬 Отзывов с текстом: {data.get('text_reviews', 0)}\n"
        f"📊 Рейтинг по звёздам:\n"
    )

    # Рейтинг по звёздам
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

    await update.message.reply_text(response, parse_mode="Markdown")

# Запуск бота
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("Бот запущен ✅")
app.run_polling()
os.environ["PORT"] = "8000"
