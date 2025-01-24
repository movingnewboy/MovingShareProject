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

        # Check if the message contains a document
        if message and message.document:
            # Modify the file name to include a prefix
            original_file_name = message.document.file_name
            modified_file_name = f"[@Tamilan_Rockers] - {original_file_name}"

            # Send the document with the modified name
            return await bot.send_document(
                chat_id=user_id,
                document=message.document.file_id,
                caption=message.caption,  # Preserve the original caption
                file_name=modified_file_name  # Add the modified file name
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
