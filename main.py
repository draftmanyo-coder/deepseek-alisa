import os
import logging
from fastapi import FastAPI, Request
import requests

app = FastAPI()

# OpenRouter API
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Модель (бесплатная)
MODEL = "meta-llama/llama-3.1-8b-instruct:free"

logging.basicConfig(level=logging.INFO)

def make_response(version, session, text, end_session=False):
    return {
        "version": version,
        "session": session,
        "response": {
            "end_session": end_session,
            "text": text,
        },
    }

@app.post("/")
async def main(request: Request):
    try:
        body = await request.json()
        user_text = body["request"]["original_utterance"]
        version = body["version"]
        session = body["session"]

        # Ответ на проверочный запрос от Яндекса
        if user_text == "ping":
            return make_response(version, session, "pong")

        if not OPENROUTER_API_KEY:
            logging.error("OPENROUTER_API_KEY не задан")
            return make_response(version, session, "Ошибка конфигурации сервера.")

        response = requests.post(
            OPENROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": user_text}],
            },
            timeout=4,  # Алиса ждёт максимум 4.5 секунды
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        return make_response(version, session, answer)

    except requests.exceptions.Timeout:
        logging.error("Таймаут при запросе к OpenRouter")
        return make_response(body["version"], body["session"], "Сейчас не могу ответить, попробуйте позже.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе к OpenRouter: {e}")
        return make_response(body["version"], body["session"], "Не удалось получить ответ.")
    except Exception as e:
        logging.error(f"Неизвестная ошибка: {e}")
        return make_response(body["version"], body["session"], "Произошла внутренняя ошибка.")
