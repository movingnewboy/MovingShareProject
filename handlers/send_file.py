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

# Helper function to replace prefixes in filenames and captions
def replace_prefix(text, new_prefix="[@Tamilan_Rocks]"):
    if text:
        # Remove any existing prefix like @something, [something], or {something}, and clean trailing chars
        text = re.sub(r"^[@\[\{]?[a-zA-Z0-9_]+[\]\}]?[\-\.\s]*", "", text)
        # Avoid duplicate prefixes
        if text.startswith(new_prefix):
            return f"**{text}**"
        # Add the new prefix with a proper separator
        return f"**{new_prefix} - {text}**"
    return f"**{new_prefix}**"


# Function to send a reply with a custom message
async def reply_forward(message: Message, file_id: int):
    try:
        reply_text = (
            f"**✅ Join Our Main Channel 👇**\n\n"
            f"**👉 Join - https://t.me/+EQti1KNCQnk5MmY1**\n\n"
            f"Files will be deleted in 12 hours to avoid copyright issues. Please forward and save them."
        )
        await message.reply_text(
            reply_text,
            disable_web_page_preview=True,
            quote=True,
        )
    except FloodWait as e:
        # Handle rate-limiting
        await asyncio.sleep(e.x)
        await reply_forward(message, file_id)


# Function to forward or send media with modified captions or filenames
async def media_forward(bot: Client, user_id: int, file_id: int):
    try:
        # Fetch the original message
        message = await bot.get_messages(chat_id=Config.DB_CHANNEL, message_ids=file_id)

        # Define media types and their send methods
        media_types = {
            "document": bot.send_document,
            "photo": bot.send_photo,
            "video": bot.send_video,
            "audio": bot.send_audio,
            "animation": bot.send_animation,
        }

        # Iterate through the media types to find the matching one
        for media_type, send_method in media_types.items():
            media = getattr(message, media_type, None)
            if media:
                # Modify filename if applicable
                file_name = None
                if media_type in ["document", "audio"] and hasattr(media, "file_name"):
                    file_name = replace_prefix(media.file_name)

                # Modify caption
                caption = replace_prefix(message.caption)

                # Send the media with updated details
                return await send_method(
                    chat_id=user_id,
                    **{media_type: media.file_id},
                    caption=caption,
                    file_name=file_name,
                )

        # Handle unsupported media types with forwarding
        if Config.FORWARD_AS_COPY:
            return await bot.copy_message(
                chat_id=user_id,
                from_chat_id=Config.DB_CHANNEL,
                message_id=file_id,
            )
        else:
            return await bot.forward_messages(
                chat_id=user_id,
                from_chat_id=Config.DB_CHANNEL,
                message_ids=file_id,
            )

    except FloodWait as e:
        # Handle Telegram's rate-limiting
        await asyncio.sleep(e.value)
        return await media_forward(bot, user_id, file_id)


# Function to send media and reply with a custom message
async def send_media_and_reply(bot: Client, user_id: int, file_id: int):
    # Forward or send media
    sent_message = await media_forward(bot, user_id, file_id)
    # Send a follow-up reply
    await reply_forward(message=sent_message, file_id=file_id)
    # Schedule message deletion after 12 hours (43200 seconds)
    asyncio.create_task(delete_after_delay(sent_message, 43200))


# Function to delete messages after a delay
async def delete_after_delay(message: Message, delay: int):
    await asyncio.sleep(delay)
    await message.delete()
