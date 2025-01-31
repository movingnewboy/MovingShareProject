import asyncio
import requests
import string
import random
from configs import Config
from pyrogram import Client
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.errors import FloodWait
from handlers.helpers import str_to_b64

def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + "" + Dic_powerN[n] + 'B'
   # formatted_size = round(size, 2) if n != 2 else int(size)
    # return f"{formatted_size:.2f}" + Dic_powerN[n] + 'B' if n != 2 else f"{formatted_size}" + Dic_powerN[n] + 'B'
   

def generate_random_alphanumeric():
    """Generate a random 8-letter alphanumeric string."""
    characters = string.ascii_letters + string.digits
    random_chars = ''.join(random.choice(characters) for _ in range(8))
    return random_chars

def get_short(url):
    rget = requests.get(f"https://{Config.SHORTLINK_URL}/api?api={Config.SHORTLINK_API}&url={url}&alias={generate_random_alphanumeric()}")
    rjson = rget.json()
    if rjson["status"] == "success" or rget.status_code == 200:
        return rjson["shortenedUrl"]
    else:
        return url

    
async def forward_to_channel(bot: Client, message: Message, editable: Message):
    try:
        __SENT = await message.forward(Config.DB_CHANNEL)
        return __SENT
    except FloodWait as sl:
        if sl.value > 45:
            await asyncio.sleep(sl.value)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text=f"#FloodWait:\nGot FloodWait of `{str(sl.value)}s` from `{str(editable.chat.id)}` !!",
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]
                    ]
                )
            )
        return await forward_to_channel(bot, message, editable)


async def save_batch_media_in_channel(bot: Client, editable: Message, message_ids: list):
    try:
        message_ids_str = ""
        file_sizes = []
        for message in (await bot.get_messages(chat_id=editable.chat.id, message_ids=message_ids)):
            sent_message = await forward_to_channel(bot, message, editable)
            if sent_message is None:
                continue
            # Check if the message contains a file and retrieve the size
            file_size = None
            if message.document:
                file_size = message.document.file_size
            elif message.video:
                file_size = message.video.file_size
            elif message.audio:
                file_size = message.audio.file_size
            
            if file_size is not None:
                file_sizes.append(file_size)
            message_ids_str += f"{str(sent_message.id)} "
            await asyncio.sleep(2)
        file_sizes.sort()
        SaveMessage = await bot.send_message(
            chat_id=Config.DB_CHANNEL,
            text=message_ids_str,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Delete Batch", callback_data="closeMessage")
            ]])
        )
        share_link = f"https://telegram.me/{Config.BOT_USERNAME}?start=Tamilan_{str_to_b64(str(SaveMessage.id))}"
        short_link = get_short(share_link)
        output_lines = [f"{humanbytes(size)} - {short_link}" for size in file_sizes]
        final_output = "\n\n".join(output_lines)
        await editable.edit(
            f"**Batch Files Stored in my Database!**\n\nHere is the Permanent Link of your files: **Sorted Files by Size:**\n<code>{final_output}</code> \n\n**Short Link - ** <code>{short_link}</code> \n\n**Original Link - ** <code>{share_link}</code> \n\n"
            f"Just Click the link to get your files!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Original Link", url=share_link),
                  InlineKeyboardButton("Short Link", url=short_link)]]
            ),
            disable_web_page_preview=True
        )
        await bot.send_message(
            chat_id=int(Config.LOG_CHANNEL),
            text=f"#BATCH_SAVE:\n\n[{editable.reply_to_message.from_user.first_name}](tg://user?id={editable.reply_to_message.from_user.id}) Got Batch Link!",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Original Link", url=short_link),
                                                InlineKeyboardButton("Short Link", url=share_link)]])
        )
    except Exception as err:
        await editable.edit(f"Something Went Wrong!\n\n**Error:** `{err}`")
        await bot.send_message(
            chat_id=int(Config.LOG_CHANNEL),
            text=f"#ERROR_TRACEBACK:\nGot Error from `{str(editable.chat.id)}` !!\n\n**Traceback:** `{err}`",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]
                ]
            )
        )


async def save_media_in_channel(bot: Client, editable: Message, message: Message):
    try:
        forwarded_msg = await message.forward(Config.DB_CHANNEL)
        file_er_id = str(forwarded_msg.id)

        # get media type
        media = message.document or message.video or message.audio or message.photo
        
        # get file name
        file_name = media.file_name if media.file_name else ""
        
        # get file size
        file_size = humanbytes(media.file_size)
        
        await forwarded_msg.reply_text(
            f"#PRIVATE_FILE:\n\n[{message.from_user.first_name}](tg://user?id={message.from_user.id}) Got File Link!",
            disable_web_page_preview=True)
        share_link = f"https://telegram.me/{Config.BOT_USERNAME}?start=Tamilan_{str_to_b64(file_er_id)}"
        short_link = get_short(share_link)
        await editable.edit(
            "**Your File Stored in my Database!**\n\n"
            f"{file_name} - {file_size} \n\n**Short Link - ** <code>{file_size} - {short_link}</code> \n\n**Original Link - ** <code>{file_size} - {share_link}</code> \n\n"
            "Just Click the link to get your file!",
            reply_markup=InlineKeyboardMarkup(
               [[InlineKeyboardButton("Original Link", url=share_link),
                  InlineKeyboardButton("Short Link", url=short_link)]]
            ),
            disable_web_page_preview=True
        )
    except FloodWait as sl:
        if sl.value > 45:
            print(f"Sleep of {sl.value}s caused by FloodWait ...")
            await asyncio.sleep(sl.value)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text="#FloodWait:\n"
                     f"Got FloodWait of `{str(sl.value)}s` from `{str(editable.chat.id)}` !!",
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]
                    ]
                )
            )
        await save_media_in_channel(bot, editable, message)
    except Exception as err:
        await editable.edit(f"Something Went Wrong!\n\n**Error:** `{err}`")
        await bot.send_message(
            chat_id=int(Config.LOG_CHANNEL),
            text="#ERROR_TRACEBACK:\n"
                 f"Got Error from `{str(editable.chat.id)}` !!\n\n"
                 f"**Traceback:** `{err}`",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Ban User", callback_data=f"ban_user_{str(editable.chat.id)}")]
                ]
            )
        )
