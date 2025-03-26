import os
from mistralai import Mistral
from django.conf import settings
from .prompts import MISTRAL_REVIEW_PROMPT

MISTRAL_API_KEY = settings.MISTRAL_API_KEY
MISTRAL_MODEL = settings.MISTRAL_MODEL

def check_review(review_text):
    # Инициализация клиента
    client = Mistral(api_key=MISTRAL_API_KEY)
    prompt = MISTRAL_REVIEW_PROMPT.format(review_text=review_text)
    chat_response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    response_text = chat_response.choices[0].message.content.lower()
    # Вывод в консоль ответа
    print(response_text)
    if "true" in response_text.lower():
        return True
    elif "false" in response_text.lower():
        return False
    else:
        return False