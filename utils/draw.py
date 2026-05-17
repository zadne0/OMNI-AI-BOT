import aiohttp
import urllib.parse

async def generate_image(prompt: str):
    # Кодируем текст, чтобы пробелы и кириллица не сломали ссылку
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Ссылка на генератор. Используем модель flux для лучшего качества
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&seed=42"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read() # Возвращаем картинку в байтах
            return None