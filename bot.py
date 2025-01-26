# (c) @TeleRoidGroup || @PredatorHackerzZ

import requests
import os
import asyncio
import traceback
import time
import string
import random
from binascii import (
    Error
)
from pyrogram import (
    Client,
    enums,
    filters
)
from pyrogram.errors import (
    UserNotParticipant,
    FloodWait,
    QueryIdInvalid
)
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message
)
from configs import Config
from handlers.database import db
from handlers.add_user_to_db import add_user_to_database
from handlers.send_file import send_media_and_reply
from handlers.helpers import b64_to_str, str_to_b64
from handlers.check_user_status import handle_user_status
from handlers.force_sub_handler import (
    handle_force_sub,
    get_invite_link,
    subscribed
)
from handlers.broadcast_handlers import main_broadcast_handler
from handlers.save_media import (
    save_media_in_channel,
    save_batch_media_in_channel
)

# Dictionary to store media for users
MediaList = {}
# Dictionary to store the timestamp of when a user started sending files
UserTimers = {}

# The time window for accepting files is 5 seconds
TIME_WINDOW = 2
token_start_time = None  # Token to track the batch start time
TOKEN_EXPIRATION = 2  # Token expiration time in seconds

Bot = Client(
    name=Config.BOT_USERNAME,
    in_memory=True,
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)


@Bot.on_message(filters.private)
async def _(bot: Client, cmd: Message):
    await handle_user_status(bot, cmd)

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):

    if True:
        invite = await client.create_chat_invite_link(
            chat_id=Config.UPDATES_CHANNEL,
            creates_join_request=True
        )
        ButtonUrl = invite.invite_link
    else:
        ButtonUrl = client.invitelink

    buttons = [
        [
            InlineKeyboardButton(
                "Join Channel",
                url = ButtonUrl)
        ]
    ]

    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.me.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = Config.FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )
    
    # channel_chat_id = int(Config.UPDATES_CHANNEL)

    # invite = await client.create_chat_invite_link(
    #         chat_id=FORCE_SUB_CHANNEL,
    #         creates_join_request=True
    #     )
    
    # invite_link = await get_invite_link(client, chat_id=channel_chat_id)
    
    # invite_link = await client.create_chat_invite_link(chat_id=chat_id)
    # await client.send_message(
    #         chat_id=cmd.from_user.id,
    #         text="**Please Join My Updates Channel to use this Bot!**\n\n"
    #              "Due to Overload, Only Channel Subscribers can use this Bot!",
    #         reply_markup=InlineKeyboardMarkup(
    #             [
    #                 [
    #                     InlineKeyboardButton("🤖 Join Updates Channel", url=invite_link.invite_link)
    #                 ],
    #                 [
    #                     InlineKeyboardButton("🔄 Refresh 🔄", callback_data="refreshForceSub")
    #                 ]
    #             ]
    #         )
    #     )
    # await message.reply(
    #     text="**Please Join My Updates Channel to use this Bot!**\n\n"
    #              "Due to Overload, Only Channel Subscribers can use this Bot!",
    #     reply_markup=InlineKeyboardMarkup(
    #         [
    #             [
    #                 InlineKeyboardButton("🤖 Join Updates Channel", url=invite_link.invite_link)
    #             ],
    #             [
    #                 InlineKeyboardButton(text = 'Try Again',
    #                 url = f"https://t.me/{Config.BOT_USERNAME}?start={message.command[1]}")
    #             ]
    #         ]
    #     ),
    #     quote = True,
    #     disable_web_page_preview = True
    # )

@Bot.on_message(filters.command("start") & filters.private & subscribed)
async def start(bot: Client, cmd: Message):

    if cmd.from_user.id in Config.BANNED_USERS:
        await cmd.reply_text("Sorry, You are banned.")
        return
    if Config.UPDATES_CHANNEL is not None:
        return
        # back = await handle_force_sub(bot, cmd)
        # if back == 400:
        #     return
    
    usr_cmd = cmd.text.split("_", 1)[-1]
    if usr_cmd == "/start":
        await add_user_to_database(bot, cmd)
        await cmd.reply_text(
            Config.HOME_TEXT.format(cmd.from_user.first_name, cmd.from_user.id),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✅ Main Channel", url="https://t.me/Quality_LinksZ")
                    ],
                    [
                        InlineKeyboardButton("👍 Support Group", url="https://t.me/Quality_LinksZ"),
                        InlineKeyboardButton("🥳 Other Channels", url="https://t.me/Team_RockerS")
                    ]
                ]
            )
        )
    else:
        try:
            try:
                file_id = int(b64_to_str(usr_cmd).split("_")[-1])
            except (Error, UnicodeDecodeError):
                file_id = int(usr_cmd.split("_")[-1])
            GetMessage = await bot.get_messages(chat_id=Config.DB_CHANNEL, message_ids=file_id)
            message_ids = []
            file_data = []  # To store (file_size, message_id) tuples
            if GetMessage.text:
                message_ids = GetMessage.text.split(" ")
                _response_msg = await cmd.reply_text(
                    text=f"**Total Files:** `{len(message_ids)}`",
                    quote=True,
                    disable_web_page_preview=True
                )
            else:
                message_ids.append(int(GetMessage.id))
            # Retrieve file sizes and store them along with message IDs
            for msg_id in message_ids:
                message = await bot.get_messages(chat_id=Config.DB_CHANNEL, message_ids=int(msg_id))
                if message.document:
                    file_size = message.document.file_size
                elif message.video:
                    file_size = message.video.file_size
                elif message.audio:
                    file_size = message.audio.file_size
                else:
                    file_size = None
                
                if file_size is not None:
                    file_data.append((file_size, msg_id))
            
            # Sort the files by size (ascending order)
            file_data.sort(key=lambda x: x[0])

             # Extract sorted message IDs
            sorted_message_ids = [msg_id for _, msg_id in file_data]
            
            # Send files in sorted order
            # for file_size, msg_id in file_data:
            #     await send_media_and_reply(bot, user_id=cmd.from_user.id, file_id=int(msg_id))
            await send_media_and_reply(bot, user_id=cmd.from_user.id, file_ids=sorted_message_ids)
        except Exception as err:
            await cmd.reply_text(f"Something went wrong!\n\n**Error:** `{err}`")

@Bot.on_message((filters.document | filters.video | filters.audio | filters.photo) & ~filters.chat(Config.DB_CHANNEL))
async def main(bot: Client, message: Message):
    
    global token_start_time
    user_id = str(message.from_user.id)
    if message.chat.type == enums.ChatType.PRIVATE:
        
        await add_user_to_database(bot, message)

        if Config.UPDATES_CHANNEL is not None:
            return
            # back = await handle_force_sub(bot, message)
            # if back == 400:
            #     return

        if message.from_user.id in Config.BANNED_USERS:
            await message.reply_text("Sorry, You are banned!\n\nContact [𝙎𝙪𝙥𝙥𝙤𝙧𝙩 𝙂𝙧𝙤𝙪𝙥](https://t.me/Quality_LinksZ)",
                                     disable_web_page_preview=True)
            return

        if Config.OTHER_USERS_CAN_SAVE_FILE is False:
            return

        # Check if the user has a timer running
        if user_id in UserTimers and time.time() - UserTimers[user_id] < TIME_WINDOW:
            # User is within the 5-second window, add file to the batch
            if MediaList.get(user_id) is None:
                MediaList[user_id] = []
            file_id = message.id  # Adjust based on the file type (document, photo, etc.)
            MediaList[user_id].append(file_id)
    
        else:
            # If it's a new batch, start a new timer
            UserTimers[user_id] = time.time()
            MediaList[user_id] = [message.id]  # Add the first file

        current_time = time.time()
        if token_start_time is None:  # First file, initialize the token
            token_start_time = current_time

        # Wait for 5 seconds, then generate the batch link
        await asyncio.sleep(TOKEN_EXPIRATION)
        message_ids = MediaList.get(f"{str(message.from_user.id)}", None)

        # Check if the token has expired (no new files during the wait period)
        if token_start_time is not None:  # Ensure no other files were added
            token_start_time = None
            await message.reply_text("Please wait, generating batch link ...", disable_web_page_preview=True)
            # await save_batch_media_in_channel(bot, message, user_id)  # Generate the batch link
            await save_batch_media_in_channel(bot=bot, editable=message, user_id=user_id, MediaList=MediaList)  # Generate the batch link
            MediaList[user_id] = []  # Reset the token and clear the batch

    elif message.chat.type == enums.ChatType.CHANNEL:
        if (message.chat.id == int(Config.LOG_CHANNEL)) or (message.chat.id == int(Config.UPDATES_CHANNEL)) or message.forward_from_chat or message.forward_from:
            return
        elif int(message.chat.id) in Config.BANNED_CHAT_IDS:
            await bot.leave_chat(message.chat.id)
            return
        else:
            pass

        try:
            forwarded_msg = await message.forward(Config.DB_CHANNEL)
            file_er_id = str(forwarded_msg.id)
            share_link = f"https://t.me/{Config.BOT_USERNAME}?start=VJBotz_{str_to_b64(file_er_id)}"
            CH_edit = await bot.edit_message_reply_markup(message.chat.id, message.id,
                                                          reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                                                              "Get Sharable Link", url=share_link)]]))
            if message.chat.username:
                await forwarded_msg.reply_text(
                    f"#CHANNEL_BUTTON:\n\n[{message.chat.title}](https://t.me/{message.chat.username}/{CH_edit.id}) Channel's Broadcasted File's Button Added!")
            else:
                private_ch = str(message.chat.id)[4:]
                await forwarded_msg.reply_text(
                    f"#CHANNEL_BUTTON:\n\n[{message.chat.title}](https://t.me/c/{private_ch}/{CH_edit.id}) Channel's Broadcasted File's Button Added!")
        except FloodWait as sl:
            await asyncio.sleep(sl.value)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text=f"#FloodWait:\nGot FloodWait of `{str(sl.value)}s` from `{str(message.chat.id)}` !!",
                disable_web_page_preview=True
            )
        except Exception as err:
            await bot.leave_chat(message.chat.id)
            await bot.send_message(
                chat_id=int(Config.LOG_CHANNEL),
                text=f"#ERROR_TRACEBACK:\nGot Error from `{str(message.chat.id)}` !!\n\n**Traceback:** `{err}`",
                disable_web_page_preview=True
            )
            
# Function to send a message to all users
async def broadcast_message(bot: Client, message: Message):
    all_users = await db.get_all_users()  # Fetch all user IDs from your database
    total_users = 0
    success = 0
    failed = 0
    
    # Store the message IDs and user IDs for deletion
    sent_messages = []

    async for user in all_users:
        try:
            sent_message = await message.copy(chat_id=int(user['id']))  # Copy and send the message
            sent_messages.append((user['id'], sent_message.id))  # Store user ID and message ID
            success += 1
        except Exception as e:
            print(f"Failed to send message to {user['id']}: {e}")
            failed += 1
        total_users += 1

    # Schedule a task to delete the messages after 12 hours
    asyncio.create_task(schedule_deletion(bot, sent_messages, delay=43200))

async def schedule_deletion(bot: Client, messages: list, delay: int):
    """  
    Schedules deletion of messages after a given delay.
    Args:
        bot (Client): The bot instance.
        messages (list): List of tuples containing user_id and message_id.
        delay (int): Delay in seconds before deletion. 
    """
    await asyncio.sleep(delay)  # Wait for the specified delay

    for user_id, msg_id in messages:
        try:
            await bot.delete_messages(chat_id=user_id, message_ids=msg_id)
            print(f"Deleted message {msg_id} for user {user_id}")
        except Exception as e:
            print(f"Failed to delete message {msg_id} for user {user_id}: {e}")

# Detect messages from the specified channel
@Bot.on_message(filters.chat(Config.CHANNEL_ID))
async def handle_channel_message(bot: Client, message: Message):
    #await main_broadcast_handler(message, db)
   print(f"New message from channel: {message.text or 'Media Content'}")
   await broadcast_message(bot, message)  # Broadcast the message to all users
        
@Bot.on_message(filters.private & filters.command("broadcast") & filters.user(Config.BOT_OWNER) & filters.reply)
async def broadcast_handler_open(_, m: Message):
    await main_broadcast_handler(m, db)


@Bot.on_message(filters.private & filters.command("status") & filters.user(Config.BOT_OWNER))
async def sts(_, m: Message):
    total_users = await db.total_users_count()
    await m.reply_text(
        text=f"**Total Users in DB:** `{total_users}`",
        quote=True
    )


@Bot.on_message(filters.private & filters.command("ban_user") & filters.user(Config.BOT_OWNER))
async def ban(c: Client, m: Message):
    
    if len(m.command) == 1:
        await m.reply_text(
            f"Use this command to ban any user from the bot.\n\n"
            f"Usage:\n\n"
            f"`/ban_user user_id ban_duration ban_reason`\n\n"
            f"Eg: `/ban_user 1234567 28 You misused me.`\n"
            f"This will ban user with id `1234567` for `28` days for the reason `You misused me`.",
            quote=True
        )
        return

    try:
        user_id = int(m.command[1])
        ban_duration = int(m.command[2])
        ban_reason = ' '.join(m.command[3:])
        ban_log_text =f"Banning user {user_id} for {ban_duration} days for the reason {ban_reason}."
        try:
            await c.send_message(
                user_id,
                f"You are banned to use this bot for **{ban_duration}** day(s) for the reason __{ban_reason}__ \n\n"
                f"**Message from the admin**"
            )
            ban_log_text += '\n\nUser notified successfully!'
        except:
            traceback.print_exc()
            ban_log_text += f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"

        await db.ban_user(user_id, ban_duration, ban_reason)
        print(ban_log_text)
        await m.reply_text(
            ban_log_text,
            quote=True
        )
    except:
        traceback.print_exc()
        await m.reply_text(
            f"Error occoured! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )


@Bot.on_message(filters.private & filters.command("unban_user") & filters.user(Config.BOT_OWNER))
async def unban(c: Client, m: Message):

    if len(m.command) == 1:
        await m.reply_text(
            f"Use this command to unban any user.\n\n"
            f"Usage:\n\n`/unban_user user_id`\n\n"
            f"Eg: `/unban_user 1234567`\n"
            f"This will unban user with id `1234567`.",
            quote=True
        )
        return

    try:
        user_id = int(m.command[1])
        unban_log_text = f"Unbanning user {user_id}"
        try:
            await c.send_message(
                user_id,
                f"Your ban was lifted!"
            )
            unban_log_text += '\n\nUser notified successfully!'
        except:
            traceback.print_exc()
            unban_log_text += f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"
        await db.remove_ban(user_id)
        print(unban_log_text)
        await m.reply_text(
            unban_log_text,
            quote=True
        )
    except:
        traceback.print_exc()
        await m.reply_text(
            f"Error occurred! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )


@Bot.on_message(filters.private & filters.command("banned_users") & filters.user(Config.BOT_OWNER))
async def _banned_users(_, m: Message):
    
    all_banned_users = await db.get_all_banned_users()
    banned_usr_count = 0
    text = ''

    async for banned_user in all_banned_users:
        user_id = banned_user['id']
        ban_duration = banned_user['ban_status']['ban_duration']
        banned_on = banned_user['ban_status']['banned_on']
        ban_reason = banned_user['ban_status']['ban_reason']
        banned_usr_count += 1
        text += f"> **user_id**: `{user_id}`, **Ban Duration**: `{ban_duration}`, " \
                f"**Banned on**: `{banned_on}`, **Reason**: `{ban_reason}`\n\n"
    reply_text = f"Total banned user(s): `{banned_usr_count}`\n\n{text}"
    if len(reply_text) > 4096:
        with open('banned-users.txt', 'w') as f:
            f.write(reply_text)
        await m.reply_document('banned-users.txt', True)
        os.remove('banned-users.txt')
        return
    await m.reply_text(reply_text, True)


@Bot.on_message(filters.private & filters.command("clear_batch"))
async def clear_user_batch(bot: Client, m: Message):
    MediaList[f"{str(m.from_user.id)}"] = []
    await m.reply_text("Cleared your batch files successfully!")


@Bot.on_callback_query()
async def button(bot: Client, cmd: CallbackQuery):

    cb_data = cmd.data
    if "aboutbot" in cb_data:
        await cmd.message.edit(
            Config.ABOUT_BOT_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Source Codes of Bot",
                                             url="https://youtube.com/@Tech_VJ")
                    ],
                    [
                        InlineKeyboardButton("Go Home", callback_data="gotohome"),
                        InlineKeyboardButton("About Dev", callback_data="aboutdevs")
                    ]
                ]
            )
        )

    elif "aboutdevs" in cb_data:
        await cmd.message.edit(
            Config.ABOUT_DEV_TEXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Source Codes of Bot",
                                             url="https://youtube.com/@Tech_VJ")
                    ],
                    [
                        InlineKeyboardButton("About Bot", callback_data="aboutbot"),
                        InlineKeyboardButton("Go Home", callback_data="gotohome")
                    ]
                ]
            )
        )

    elif "gotohome" in cb_data:
        await cmd.message.edit(
            Config.HOME_TEXT.format(cmd.message.chat.first_name, cmd.message.chat.id),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Updates Channel", url="https://t.me/Quality_LinksZ")
                    ],
                    [
                        InlineKeyboardButton("About Bot", callback_data="aboutbot"),
                        InlineKeyboardButton("About Dev", callback_data="aboutdevs"),
                        InlineKeyboardButton("Close 🚪", callback_data="closeMessage")
                    ],
                    [
                        InlineKeyboardButton("Support Group", url="https://t.me/Quality_LinksZ"),
                        InlineKeyboardButton("YouTube Channel", url="https://youtube.com/@Tech_VJ")
                    ]
                ]
            )
        )

    elif "refreshForceSub" in cb_data:
        if Config.UPDATES_CHANNEL:
            if Config.UPDATES_CHANNEL.startswith("-100"):
                channel_chat_id = int(Config.UPDATES_CHANNEL)
            else:
                channel_chat_id = Config.UPDATES_CHANNEL
            try:
                # user = await bot.get_chat_member(channel_chat_id, cmd.message.chat.id) # was giving error
                user = await bot.get_chat_member(chat_id=channel_chat_id, user_id=cmd.from_user.id)
                if user.status == "kicked":
                    await cmd.message.edit(
                        text="Sorry Sir, You are Banned to use me. Contact my [𝙎𝙪𝙥𝙥𝙤𝙧𝙩 𝙂𝙧𝙤𝙪𝙥](https://t.me/Quality_LinksZ).",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                # invite_link = await get_invite_link(channel_chat_id) # was giving error
                invite_link = await get_invite_link(bot=bot, chat_id=channel_chat_id)
                await cmd.message.edit(
                    text="**I like Your Smartness But Don't Be Oversmart! 😑**\n\n",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🤖 Join Updates Channel", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton("🔄 Refresh 🔄", callback_data="refreshmeh")
                            ]
                        ]
                    )
                )
                return
            except Exception:
                await cmd.message.edit(
                    text="Something went Wrong. Contact my [𝙎𝙪𝙥𝙥𝙤𝙧𝙩 𝙂𝙧𝙤𝙪𝙥](https://t.me/Quality_LinksZ)",
                    disable_web_page_preview=True
                )
                return
        await cmd.message.edit(
            text=Config.HOME_TEXT.format(cmd.message.chat.first_name, cmd.message.chat.id),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✅ Main Channel", url="https://t.me/Quality_LinksZ")
                    ],
                    [
                        InlineKeyboardButton("👍 Support Group", url="https://t.me/Quality_LinksZ"),
                        InlineKeyboardButton("🥳 Other Channels", url="https://t.me/Team_RockerS")
                    ]
                ]
            )
        )

    elif cb_data.startswith("ban_user_"):
        user_id = cb_data.split("_", 2)[-1]
        if Config.UPDATES_CHANNEL is None:
            await cmd.answer("Sorry Sir, You didn't Set any Updates Channel!", show_alert=True)
            return
        if not int(cmd.from_user.id) == Config.BOT_OWNER:
            await cmd.answer("You are not allowed to do that!", show_alert=True)
            return
        try:
            await bot.kick_chat_member(chat_id=int(Config.UPDATES_CHANNEL), user_id=int(user_id))
            await cmd.answer("User Banned from Updates Channel!", show_alert=True)
        except Exception as e:
            await cmd.answer(f"Can't Ban Him!\n\nError: {e}", show_alert=True)

    elif "addToBatchTrue" in cb_data:
        if MediaList.get(f"{str(cmd.from_user.id)}", None) is None:
            MediaList[f"{str(cmd.from_user.id)}"] = []
        file_id = cmd.message.reply_to_message.id
        MediaList[f"{str(cmd.from_user.id)}"].append(file_id)
        await cmd.message.edit("File Saved in Batch!\n\n"
                               "Press below button to get batch link.",
                               reply_markup=InlineKeyboardMarkup([
                                   [InlineKeyboardButton("Get Batch Link", callback_data="getBatchLink")],
                                   [InlineKeyboardButton("Close Message", callback_data="closeMessage")]
                               ]))

    elif "addToBatchFalse" in cb_data:
        await save_media_in_channel(bot, editable=cmd.message, message=cmd.message.reply_to_message)

    elif "getBatchLink" in cb_data:
        message_ids = MediaList.get(f"{str(cmd.from_user.id)}", None)
        if message_ids is None:
            await cmd.answer("Batch List Empty!", show_alert=True)
            return
        await cmd.message.edit("Please wait, generating batch link ...")
        await save_batch_media_in_channel(bot=bot, editable=cmd.message, message_ids=message_ids)
        MediaList[f"{str(cmd.from_user.id)}"] = []

    elif "closeMessage" in cb_data:
        await cmd.message.delete(True)

    try:
        await cmd.answer()
    except QueryIdInvalid: pass


Bot.run()
