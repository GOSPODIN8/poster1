import logging
import random

from google import genai
from google.genai import types

import config

logger = logging.getLogger(__name__)

client = genai.Client(api_key=config.GEMINI_API_KEY)

# Разные формулировки CTA, чтобы прогрев не выглядел как спам одним и тем же текстом
CTA_STYLES = [
    "мягкий (просто упомянуть, что в закрытом клубе разбираем такие темы глубже)",
    "через любопытство (намекнуть, что в клубе есть кейсы/цифры, которых нет в канале)",
    "через ограниченность (в клубе разбираются свежие связки, которые быстро выгорают)",
    "через сообщество (в клубе люди поддерживают друг друга и обмениваются опытом)",
]

TEXT_PROMPT_TEMPLATE = """Ты — автор Telegram-канала про дропшиппинг для русскоязычной аудитории (бренд «Эдриан Трейп»).

Придумай ОДИН короткий, полезный пост для канала (гайд, лайфхак или разбор ниши в дропшиппинге).
Требования:
- Язык: русский
- Длина: 500-900 символов
- Формат: living-текст с эмодзи по смыслу (не перебарщивай), можно короткие абзацы или список
- В конце поста — мягкий призыв вступить в закрытый клуб «Клуб Единомышленников», где разбираются темы глубже.
  Стиль призыва: {cta_style}.
  Ссылку вставь ТОЧНО в таком виде: {club_link}
- Не используй Markdown-разметку (**, __ и т.п.), только обычный текст и эмодзи, т.к. пост отправляется как HTML caption в Telegram
- Не повторяй одну и ту же тему каждый раз — выбери случайную конкретную подтему дропшиппинга (ниши, поставщики, реклама, воронки, психология продаж, ошибки новичков, автоматизация и т.д.)

Верни ТОЛЬКО текст поста, без заголовков вида "Пост:" и без кавычек."""

IMAGE_PROMPT_TEMPLATE = """A clean, modern, professional illustration for a social media post about dropshipping and e-commerce business, topic: {topic_hint}.
Style: flat design, minimal, bright colors, business/tech aesthetic, no text or letters in the image, no logos, 16:9 aspect ratio."""


def generate_post_text() -> str:
    cta_style = random.choice(CTA_STYLES)
    prompt = TEXT_PROMPT_TEMPLATE.format(cta_style=cta_style, club_link=config.CLUB_BOT_LINK)

    response = client.models.generate_content(
        model=config.TEXT_MODEL,
        contents=prompt,
    )
    text = response.text.strip()
    return text


def generate_post_image(topic_hint: str) -> bytes | None:
    prompt = IMAGE_PROMPT_TEMPLATE.format(topic_hint=topic_hint)
    try:
        response = client.models.generate_content(
            model=config.IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["Text", "Image"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data
    except Exception:
        logger.exception("Не удалось сгенерировать изображение, пост уйдёт без картинки")
    return None


def generate_post() -> tuple[str, bytes | None]:
    text = generate_post_text()
    image_bytes = generate_post_image(text[:120])
    return text, image_bytes

