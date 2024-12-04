import asyncio
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен из переменной окружения
tg_token = os.getenv("TG_BOT_TOKEN")

# Проверка наличия токена
if tg_token is None:
    raise ValueError("Токен не найден! Убедитесь, что в файле .env указан правильный токен.")

# Инициализация бота
bot = Bot(token=tg_token)
dp = Dispatcher()

# Хранение состояния пользователя
user_data = {}

# Функция для проверки корректности email
def is_valid_email(email: str) -> bool:
    # Здесь можно добавить реальную проверку email, например, через регулярные выражения
    return '@' in email

# Обработчик команды /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Пожалуйста, введите ваш email:")

# Обработчик для email
@dp.message(lambda message: not getattr(message.from_user, 'email', None) and not user_data.get(message.from_user.id, {}).get('email', None))
async def get_email(message: Message):
    email = message.text
    if is_valid_email(email):
        await message.answer(f"Ваш email: {email}. Теперь введите текст сообщения для отправки.")
        # Сохраняем email для дальнейшего использования
        user_data[message.from_user.id] = {'email': email, 'waiting_for_message': True}
    else:
        await message.answer("Некорректный email. Пожалуйста, попробуйте снова.")

# Обработчик для текста сообщения
@dp.message(lambda message: user_data.get(message.from_user.id, {}).get('waiting_for_message', False))
async def get_message_text(message: Message):
    # Получаем email из контекста пользователя
    email = user_data.get(message.from_user.id, {}).get('email')
    if not email:
        await message.answer("Сначала введите правильный email.")
        return

    # Сохраняем текст сообщения
    message_text = message.text
    await message.answer("Отправляю сообщение...")

    # Отправляем email через SMTP
    send_email(email, message_text)
    
    # Помечаем, что сообщение отправлено и процесс завершен
    user_data[message.from_user.id]['waiting_for_message'] = False
    await message.answer("Сообщение успешно отправлено!")

# Функция отправки email через SMTP
def send_email(to_email: str, message_text: str):
    from_email = os.getenv("YAND_EMAIL")
    password = os.getenv("YAND_PASSWORD")
    
    if not from_email or not password:
        raise ValueError("Не указаны данные для SMTP (email или пароль)")

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Сообщение от бота"

    msg.attach(MIMEText(message_text, 'plain'))

    # Подключаемся к SMTP серверу Яндекса
    try:
        with smtplib.SMTP('smtp.yandex.ru', 587) as server:
            server.starttls()
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
    except Exception as e:
        print(f"Ошибка отправки email: {e}")

# Основная асинхронная функция
async def main():
    # Запускаем polling
    await dp.start_polling(bot)

# Запуск
if __name__ == "__main__":
    asyncio.run(main())
