import os
import logging
from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Новый адрес API и ключ из переменной окружения
LLM7_API_URL = "https://api.llm7.io/v1/chat/completions"
LLM7_API_KEY = os.getenv("LLM7_API_KEY") # Имя переменной, которую мы задали на Render

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

        if user_text == "ping":
            return make_response(version, session, "pong")

        if not LLM7_API_KEY:
            logging.error("LLM7_API_KEY не задан")
            # Можно использовать анонимный доступ, если ключа нет
            headers = {}
        else:
            headers = {"Authorization": f"Bearer {LLM7_API_KEY}"}

        # Новый формат запроса для LLM7.io (совместим с OpenAI)
        response = requests.post(
            LLM7_API_URL,
            headers=headers,
            json={
                "model": "default",  # LLM7.io сам выберет доступную модель (включая DeepSeek)
                "messages": [{"role": "user", "content": user_text}],
            },
            timeout=20,
        )
        response.raise_for_status()
        # Ответ приходит в стандартном формате OpenAI
        answer = response.json()["choices"][0]["message"]["content"]
        return make_response(version, session, answer)

    except requests.exceptions.Timeout:
        logging.error("Таймаут при запросе к LLM7.io")
        return make_response(body["version"], body["session"], "LLM7.io не ответил вовремя.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе к LLM7.io: {e}")
        return make_response(body["version"], body["session"], "Не удалось получить ответ от LLM7.io.")
    except Exception as e:
        logging.error(f"Неизвестная ошибка: {e}")
        return make_response(body["version"], body["session"], "Произошла внутренняя ошибка.")
