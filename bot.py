import asyncio
import io
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile

import config
import database as db
from content_generator import generate_post
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def post_to_channel():
    logger.info("Генерирую и публикую пост...")
    text = ""
    had_image = False
    try:
        text, image_bytes = generate_post()
        had_image = image_bytes is not None

        if image_bytes:
            photo = BufferedInputFile(image_bytes, filename="post.jpg")
            await bot.send_photo(chat_id=config.CHANNEL_USERNAME, photo=photo, caption=text)
        else:
            await bot.send_message(chat_id=config.CHANNEL_USERNAME, text=text)

        await db.log_post(text, had_image, success=True)
        logger.info("Пост опубликован успешно")
    except Exception as e:
        logger.exception("Ошибка при публикации поста")
        await db.log_post(text, had_image, success=False, error=str(e))
        if config.ADMIN_ID:
            try:
                await bot.send_message(config.ADMIN_ID, f"⚠️ Не удалось опубликовать пост:\n{e}")
            except Exception:
                pass


def admin_only(handler):
    async def wrapper(message: Message):
        if message.from_user.id != config.ADMIN_ID:
            return
        await handler(message)

    return wrapper


@dp.message(Command("post_now"))
@admin_only
async def cmd_post_now(message: Message):
    await message.answer("Генерирую и публикую пост, подожди немного...")
    await post_to_channel()
    await message.answer("Готово ✅")


@dp.message(Command("stats"))
@admin_only
async def cmd_stats(message: Message):
    s = await db.get_stats()

    last_lines = []
    for row in s["last_posts"]:
        date_str = datetime.fromtimestamp(row["posted_at"]).strftime("%d.%m %H:%M")
        status = "✅" if row["success"] else f"❌ {row['error'][:60]}"
        last_lines.append(f"   • {date_str} — {status}")
    last_block = "\n".join(last_lines) if last_lines else "   —"

    text = (
        f"📊 <b>Статистика прогрев-бота @adrian_trape</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ Успешных постов всего: <b>{s['total_ok']}</b>\n"
        f"❌ Ошибок всего: <b>{s['total_fail']}</b>\n"
        f"🕐 Успешных за 24ч: <b>{s['today_ok']}</b> (из {len(config.POST_TIMES_MSK)} по расписанию)\n\n"
        f"🔜 <b>Последние попытки:</b>\n{last_block}"
    )
    await message.answer(text)


async def main():
    await db.init_db()
    start_scheduler(post_to_channel)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
