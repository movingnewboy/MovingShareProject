import re
import asyncio
import requests
import string
import random
from configs import Config
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from handlers.helpers import str_to_b64

async def reply_forward(message: Message, file_id: int):
    try:
        await message.reply_text(
            f"**✅Join Our Main Channel 👇** \n\n **👉 Join - https://t.me/+EQti1KNCQnk5MmY1 ** \n\nFiles will be deleted in 12 hours to avoid copyright issues. Please forward and save them.",
            disable_web_page_preview=True,
            quote=True
        )
    except FloodWait as e:
        await asyncio.sleep(e.x)
        await reply_forward(message, file_id)

async def media_forward(bot: Client, user_id: int, file_id: int):
    try:
        # Fetch the original message
        message = await bot.get_messages(chat_id=Config.DB_CHANNEL, message_ids=file_id)

        # Helper function to modify captions and filenames
        def replace_prefix(text, new_prefix="[@Tamilan_Rocks]"):
            if text:
                # Replace any prefix like @anything, [@anything], or {anything} with the new prefix
                text = re.sub(r"^[@\[\{]?[a-zA-Z0-9_]+[\]\}]?", new_prefix, text)
                # Only append " - " if the text was modified
                if not text.startswith(new_prefix):
                    return f"**{new_prefix} - {text}**"  # Bold file name
                return f"**{text}**"  # Bold file name
            return f"**{new_prefix}**"

        # Mapping of media types to their corresponding send methods
        media_types = {
            "document": bot.send_document,
            "photo": bot.send_photo,
            "video": bot.send_video,
            "audio": bot.send_audio,
            "animation": bot.send_animation,
        }

        # Iterate through the media types to find the one that matches
        for media_type, send_method in media_types.items():
            media = getattr(message, media_type, None)
            if media:
                # Special handling for file_name in document/audio
                file_name = None
                if media_type in ["document", "audio"] and hasattr(media, "file_name"):
                    file_name = replace_prefix(media.file_name)  # Replace prefix in file name

                # Handle caption replacement
                caption = replace_prefix(message.caption)  # Replace prefix in caption

                # Send the message with the appropriate method
                return await send_method(
                    chat_id=user_id,
                    **{media_type: media.file_id},
                    caption=caption,  # Modified caption
                    file_name=file_name,  # Modified file name
                )
            
        if Config.FORWARD_AS_COPY is True:
            return await bot.copy_message(chat_id=user_id, from_chat_id=Config.DB_CHANNEL,
                                          message_id=file_id)
        elif Config.FORWARD_AS_COPY is False:
            return await bot.forward_messages(chat_id=user_id, from_chat_id=Config.DB_CHANNEL,
                                              message_ids=file_id)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return media_forward(bot, user_id, file_id)
        await message.delete()

async def send_media_and_reply(bot: Client, user_id: int, file_id: int):
    sent_message = await media_forward(bot, user_id, file_id)
    await reply_forward(message=sent_message, file_id=file_id)
    asyncio.create_task(delete_after_delay(sent_message, 43200))

async def delete_after_delay(message, delay):
    await asyncio.sleep(delay)
    await message.delete()
