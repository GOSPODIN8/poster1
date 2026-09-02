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
- Формат: используй HTML-теги <b>...</b>, чтобы выделить жирным ключевые фразы, цифры, названия ниш и важные мысли (не весь текст, а отдельные акценты — 3-5 выделений на пост)
- Уместно расставляй эмодзи по смыслу текста (в начале смысловых блоков, у списков, у выделенных фраз) — не более 1 эмодзи на предложение
- Можно короткие абзацы или список с эмодзи вместо точек
- В конце поста — мягкий призыв вступить в закрытый клуб «Клуб Единомышленников», где разбираются темы глубже.
  Стиль призыва: {cta_style}.
  Ссылку вставь ТОЧНО в таком виде: {club_link}
- Разрешены ТОЛЬКО HTML-теги <b> и </b> для жирного текста. Никакой другой разметки (**, __, #, markdown-списков) не используй — пост отправляется как HTML caption в Telegram
- Не повторяй одну и ту же тему каждый раз — выбери случайную конкретную подтему дропшиппинга (ниши, поставщики, реклама, воронки, психология продаж, ошибки новичков, автоматизация и т.д.)

Верни ТОЛЬКО текст поста, без заголовков вида "Пост:" и без кавычек."""

IMAGE_PROMPT_TEMPLATE = """Using the attached reference photo of a person, create a horizontal 16:9 promotional poster-style image featuring that exact same person — keep their face, hairstyle and identity clearly recognizable and consistent with the reference photo.

Put them in a pose, outfit and setting that fits this post topic: {topic_hint}
Vary the pose, clothing and setting each time so it doesn't look like a repeated photo — but the face must always match the reference.

Visual style: vintage halftone-print poster aesthetic, bold high-contrast limited color palette of deep red, black and cream/off-white, dramatic cinematic lighting, grainy retro print texture, strong graphic silhouette, confident/powerful business mood. No text, no letters, no logos, no watermarks anywhere in the image.

Aspect ratio: 16:9 landscape."""


REFERENCE_IMAGE_PATH = "assets/person_reference.jpg"


def _load_reference_image() -> bytes:
    with open(REFERENCE_IMAGE_PATH, "rb") as f:
        return f.read()


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
    try:
        ref_bytes = _load_reference_image()
        ref_part = types.Part.from_bytes(data=ref_bytes, mime_type="image/jpeg")

        response = client.models.generate_content(
            model=config.IMAGE_MODEL,
            contents=[ref_part, prompt],
            config=types.GenerateContentConfig(
                response_modalities=["Text", "Image"],
                image_config=types.ImageConfig(aspect_ratio="16:9"),
            ),
        )
        candidates = response.candidates or []
        if candidates and candidates[0].content and candidates[0].content.parts:
            for part in candidates[0].content.parts:
                if part.inline_data:
                    return part.inline_data.data, None
            return None, "В ответе модели не нашлось картинки (только текст)"
        return None, "Пустой ответ от модели изображений"
    except Exception as e:
        logger.exception("Не удалось сгенерировать изображение, пост уйдёт без картинки")
        return None, f"{type(e).__name__}: {e}"


def generate_post() -> tuple[str, bytes | None, str | None]:
    text = generate_post_text()
    image_bytes, image_error = generate_post_image(text[:120])
    return text, image_bytes, image_error
