import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Системный промпт (можно изменить в .env)
SYSTEM_PROMPT = os.getenv('SYSTEM_PROMPT', 'Ты полезный AI-ассистент. Отвечай на русском языке.')

# Бесплатные модели OpenRouter
FREE_MODELS = [
    "tngtech/deepseek-r1t2-chimera:free",
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Сәлем! Мен NexoGPT, жасанды интеллект қосылған телеграм ботпын!
Саған қалай көмектесе аламын?
"""
    await update.message.reply_text(welcome_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_message = update.message.text

    if not user_message.strip():
        await update.message.reply_text("Текст жазуыңызды сұраймын.")
        return

    try:
        # Показываем статус "печатает..."
        await update.message.chat.send_action(action="typing")

        # Отправляем запрос к OpenRouter API
        response = await get_ai_response(user_message)

        # Отправляем ответ пользователю
        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("Сұраныс кезінде қате пайда болды, кейінірек қайталап көріңіз.")


async def get_ai_response(prompt: str) -> str:
    """Получение ответа от OpenRouter API с бесплатными моделями"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram-bot.com",  # Required by OpenRouter
        "X-Title": "Telegram AI Bot"  # Required by OpenRouter
    }

    # Пробуем разные бесплатные модели по очереди
    for model in FREE_MODELS:
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 6000
            }

            response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=45)
            response.raise_for_status()

            data = response.json()
            if 'choices' in data and data['choices']:
                return data['choices'][0]['message']['content'].strip()

        except requests.exceptions.RequestException as e:
            logger.warning(f"Модель {model} недоступна: {e}")
            continue  # Пробуем следующую модель
        except Exception as e:
            logger.warning(f"Ошибка с моделью {model}: {e}")
            continue

    # Если все модели не сработали
    return "Қателік."


def main():
    """Основная функция"""
    if not TELEGRAM_TOKEN:
        logger.error("Не установлен TELEGRAM_TOKEN!")
        return

    if not OPENROUTER_API_KEY:
        logger.error("Не установлен OPENROUTER_API_KEY!")
        return

    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики (только старт и сообщения)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    logger.info("Бот қосылды!")
    logger.info(f"Системный промпт: {SYSTEM_PROMPT[:50]}...")
    application.run_polling()


if __name__ == "__main__":

    main()

