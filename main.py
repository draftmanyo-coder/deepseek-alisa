import os
import logging
from fastapi import FastAPI, Request
import requests

app = FastAPI()

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

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

        # Проверка на проверочный запрос "ping" от Яндекса
        if user_text == "ping":
            return make_response(version, session, "pong")

        if not DEEPSEEK_API_KEY:
            logging.error("DEEPSEEK_API_KEY не задан")
            return make_response(version, session, "Ошибка конфигурации сервера.")

        response = requests.post(
            DEEPSEEK_API_URL,
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": user_text}],
            },
            timeout=20,
        )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        return make_response(version, session, answer)

    except requests.exceptions.Timeout:
        logging.error("Таймаут при запросе к DeepSeek")
        return make_response(body["version"], body["session"], "DeepSeek не ответил вовремя.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе к DeepSeek: {e}")
        return make_response(body["version"], body["session"], "Не удалось получить ответ от DeepSeek.")
    except Exception as e:
        logging.error(f"Неизвестная ошибка: {e}")
        return make_response(body["version"], body["session"], "Произошла внутренняя ошибка.")
