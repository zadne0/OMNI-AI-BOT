from aiogram import Router, F, types
from aiogram.filters import Command
from utils.openrouter import ask_qwen, transcribe_voice, ask_gemini_vision
from utils.db import update_user_model, get_user_model, save_message, get_history
from utils.draw import generate_image
from aiogram.types import BufferedInputFile
import os

router = Router()

# Системный промпт
SYSTEM_PROMPT = {
    "role": "system", 
    "content": "Ты — Omni-Bot, крутой искин-помощник. Твоё имя Корнелий. Отвечай ВСЕГДА только на русском языке. Общайся как бро, используй сленг, будь кратким и четким."
}

# Список актуальных моделей
MODELS = {
    "🎯 Qwen 2.5 (72B)": "qwen/qwen-2.5-72b-instruct",
    "🚀 Llama 3.1 (8B)": "meta-llama/llama-3.1-8b-instruct",
    "👁 Llama 3.3 (70b)": "meta-llama/llama-3.3-70b-instruct",
}

# --- 1. Сначала команды (Самый высокий приоритет) ---

@router.message(Command("start"))
async def start(message: types.Message):
    kb = [[types.KeyboardButton(text=m)] for m in MODELS.keys()]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\nЯ OmniBot. Выбери модель:",
        reply_markup=keyboard
    )

@router.message(F.text.startswith("/draw"))
async def draw_command(message: types.Message):
    prompt = message.text[5:].strip()
    
    if not prompt:
        await message.reply("📸 Бро, напиши, что рисовать! Например: /draw кот в космосе")
        return

    wait_msg = await message.answer("🎨 Малюю... Подожди немного.")

    try:
        photo_bytes = await generate_image(prompt)
        if photo_bytes:
            input_file = BufferedInputFile(photo_bytes, filename="art.jpg")
            await message.answer_photo(photo=input_file, caption=f"🎯 По запросу: {prompt}")
            await wait_msg.delete()
        else:
            await wait_msg.edit_text("❌ Не удалось получить картинку.")
    except Exception as e:
        await wait_msg.edit_text(f"❌ Ошибка в малярке: {e}")

# --- 2. Специальные типы сообщений (Смена модели, Фото, Голос) ---

@router.message(F.text.in_(MODELS.keys()))
async def change_model(message: types.Message):
    model_id = MODELS[message.text]
    await update_user_model(message.from_user.id, model_id)
    await message.answer(f"✅ Принято! Теперь на связи {message.text}")

@router.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    wait = await message.answer("📸 Смотрю фото...")
    
    try:
        file = await message.bot.get_file(message.photo[-1].file_id)
        photo_buffer = await message.bot.download_file(file.file_path)
        image_bytes = photo_buffer.read()
        
        caption = message.caption if message.caption else "Что на фото?"
        await save_message(user_id, "user", f"[Фото]: {caption}")
        
        response = await ask_gemini_vision(image_bytes, caption)
        
        await save_message(user_id, "assistant", response)
        await wait.edit_text(response)
        
    except Exception as e:
        await wait.edit_text(f"❌ Вновь ошибка: {e}")

@router.message(F.voice)
async def handle_voice(message: types.Message):
    user_id = message.from_user.id
    model = await get_user_model(user_id)
    wait = await message.answer("👂 Слушаю внимательно...")
    
    file_id = message.voice.file_id
    file = await message.bot.get_file(file_id)
    file_on_disk = f"data/{file_id}.ogg"
    await message.bot.download_file(file.file_path, destination=file_on_disk)
    
    text_from_voice = await transcribe_voice(file_on_disk)
    if os.path.exists(file_on_disk):
        os.remove(file_on_disk)
    
    if not text_from_voice:
        await wait.edit_text("❌ Не разобрал голос.")
        return

    await save_message(user_id, "user", text_from_voice)
    history = await get_history(user_id)
    full_messages = [SYSTEM_PROMPT] + history
    
    try:
        response = await ask_qwen(full_messages, model)
        await save_message(user_id, "assistant", response)
        await wait.edit_text(f"🎤 _«{text_from_voice}»_ \n\n🤖 {response}")
    except Exception as e:
        await wait.edit_text(f"❌ Ошибка после ГС: {e}")

# --- 3. Обычный текст (Самый низкий приоритет) ---

@router.message(F.text)
async def handle_text(message: types.Message):
    # Если это любая другая команда, которую мы не обработали выше — игнорим тут
    if message.text.startswith('/'): return
    
    user_id = message.from_user.id
    model = await get_user_model(user_id)
    
    await save_message(user_id, "user", message.text)
    history = await get_history(user_id)
    full_messages = [SYSTEM_PROMPT] + history
    
    wait = await message.answer("🤖 Соображаю...")
    
    try:
        response = await ask_qwen(full_messages, model)
        await save_message(user_id, "assistant", response)
        
        if len(response) > 4000:
            for i in range(0, len(response), 4000):
                await message.answer(response[i:i+4000])
            await wait.delete()
        else:
            await wait.edit_text(response)
    except Exception as e:
        await wait.edit_text(f"❌ Мозги закипели: {e}")
