import aiohttp
import base64
import os
import subprocess
import json
import requests
from os import getenv

# --- ФУНКЦИЯ ДЛЯ ТЕКСТА И ФОТО ---
async def ask_gemini_vision(image_bytes, caption="Что на фото?"):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_KEY')}", # Юзаем ключ OpenRouter
        "Content-Type": "application/json"
    }
    
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    payload = {
        "model": "openrouter/free", 
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": caption},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                res = await resp.json()
                return res['choices'][0]['message']['content']
            else:
                err = await resp.text()
                return f"Ошибка OpenRouter Vision ({resp.status}): {err[:100]}"

async def ask_qwen(messages, model, image_bytes=None):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {getenv('OPENROUTER_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as resp:
                result = await resp.json()
                return result['choices'][0]['message']['content']
        except Exception as e:
            return f"Ошибка OpenRouter: {e}"

# --- ФУНКЦИЯ ДЛЯ ГОЛОСА ---
async def transcribe_voice(file_path: str):
    mp3_path = file_path.replace(".ogg", ".mp3")
    
    # Конвертируем
    subprocess.run(['ffmpeg', '-y', '-i', file_path, mp3_path], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not os.path.exists(mp3_path): return None

    # Настройки Groq (Возьми ключ на console.groq.com - это 1 минута)
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {getenv('GROQ_API_KEY')}"}
    
    try:
        with open(mp3_path, 'rb') as f:
            files = {'file': ('voice.mp3', f)}
            data = {'model': 'whisper-large-v3-turbo'}
            response = requests.post(url, headers=headers, files=files, data=data)
            
        if os.path.exists(mp3_path): os.remove(mp3_path)

        if response.status_code == 200:
            return response.json().get('text', '')
        return None
    except:
        return None
