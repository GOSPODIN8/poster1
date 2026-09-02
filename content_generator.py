import logging
import random
import urllib.parse

import requests
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
- Формат: используй HTML-теги <b>...</b>, чтобы выделить жирным ключевые фразы, цифры, названия ниш и важные мысли (не весь текст, а отдельные акценты — 3-5 выделений на пост)
- Уместно расставляй эмодзи по смыслу текста (в начале смысловых блоков, у списков, у выделенных фраз) — не более 1 эмодзи на предложение
- Можно короткие абзацы или список с эмодзи вместо точек
- В конце поста — мягкий призыв вступить в закрытый клуб «Клуб Единомышленников», где разбираются темы глубже.
  Стиль призыва: {cta_style}.
  Ссылку вставь ТОЧНО в таком виде: {club_link}
- Разрешены ТОЛЬКО HTML-теги <b> и </b> для жирного текста. Никакой другой разметки (**, __, #, markdown-списков) не используй — пост отправляется как HTML caption в Telegram
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


def generate_post_image(topic_hint: str) -> tuple[bytes | None, str | None]:
    prompt = IMAGE_PROMPT_TEMPLATE.format(topic_hint=topic_hint)
    gemini_error = None

    try:
        response = client.models.generate_content(
            model=config.IMAGE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["Text", "Image"],
            ),
        )
        candidates = response.candidates or []
        if candidates and candidates[0].content and candidates[0].content.parts:
            for part in candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data, None
            gemini_error = "В ответе модели не нашлось картинки (только текст)"
        else:
            gemini_error = "Пустой ответ от модели изображений"
    except Exception as e:
        logger.warning(f"Gemini image gen не сработал ({e}), пробую запасной вариант")
        gemini_error = f"{type(e).__name__}: {e}"

    # Запасной вариант: бесплатный сервис без API-ключа и лимитов биллинга
    image_bytes, fallback_error = generate_post_image_fallback(prompt)
    if image_bytes:
        return image_bytes, None

    return None, f"Gemini: {gemini_error}; запасной вариант: {fallback_error}"


def generate_post_image_fallback(prompt: str) -> tuple[bytes | None, str | None]:
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=576&nologo=true"
        resp = requests.get(url, timeout=45)
        resp.raise_for_status()
        return resp.content, None
    except Exception as e:
        logger.exception("Запасной генератор картинок тоже не сработал")
        return None, f"{type(e).__name__}: {e}"


def generate_post() -> tuple[str, bytes | None, str | None]:
    text = generate_post_text()
    image_bytes, image_error = generate_post_image(text[:120])
    return text, image_bytes, image_error

