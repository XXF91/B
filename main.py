import pyrogram
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import time
import os
import threading
import sys
from os import environ

# بيانات البوت
api_hash = "33a37e968712427c2e7971cb03f341b3"
api_id = "15523035"
bot_token = "7473745729:AAGJE4wbu5eURdu8zWMRtHVEimQ7140_6z0"
bot = Client("mybot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# المسار إلى الصورة المصغرة الافتراضية
DEFAULT_THUMBNAIL = "default_thumb.jpg"

# متغيرات لإدارة العمليات
active_downloads = {}
active_uploads = {}

# download status
async def downstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
    time.sleep(3)      
    while os.path.exists(statusfile):
        with open(statusfile, "r") as downread:
            txt = downread.read()
        try:
            await bot.edit_message_text(message.chat.id, message.id, f"__Downloaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)

# upload status
async def upstatus(statusfile, message):
    while True:
        if os.path.exists(statusfile):
            break
    time.sleep(3)      
    while os.path.exists(statusfile):
        with open(statusfile, "r") as upread:
            txt = upread.read()
        try:
            await bot.edit_message_text(message.chat.id, message.id, f"__Uploaded__ : **{txt}**")
            time.sleep(10)
        except:
            time.sleep(5)

# progress writer
def progress(current, total, message, type):
    with open(f'{message.id}{type}status.txt', "w") as fileup:
        fileup.write(f"{current * 100 / total:.1f}%")

# start command
@bot.on_message(filters.command(["start"]))
async def send_start(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    await bot.send_message(
        message.chat.id,
        f"**__👋 Hi** **{message.from_user.mention}**, **I am a bot that can download restricted content from channels or groups I am a member of.__**\n\n{USAGE}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 OWNER", url="https://t.me/X_XF8")]]),
        reply_to_message_id=message.id
    )

# cancel command
@bot.on_message(filters.command(["cancel"]))
async def cancel_operations(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    if message.chat.id in active_downloads:
        active_downloads[message.chat.id] = False  # إيقاف التحميل
        await bot.send_message(message.chat.id, "**تم إيقاف التحميل.**", reply_to_message_id=message.id)
    if message.chat.id in active_uploads:
        active_uploads[message.chat.id] = False  # إيقاف الرفع
        await bot.send_message(message.chat.id, "**تم إيقاف الرفع.**", reply_to_message_id=message.id)

# restart command
@bot.on_message(filters.command(["restart"]))
async def restart_bot(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    await bot.send_message(message.chat.id, "**جارٍ إعادة تشغيل البوت...**", reply_to_message_id=message.id)
    os.execv(sys.executable, [sys.executable, __file__])  # إعادة تشغيل البوت

@bot.on_message(filters.text)
async def save(client: pyrogram.client.Client, message: pyrogram.types.messages_and_media.message.Message):
    print(message.text)

    # getting message
    if "https://t.me/" in message.text:
        datas = message.text.split("/")
        temp = datas[-1].replace("?single", "").split("-")
        fromID = int(temp[0].strip())
        try: toID = int(temp[1].strip())
        except: toID = fromID

        for msgid in range(fromID, toID + 1):
            # public or private
            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])
                await handle_private(message, chatid, msgid)
            else:
                username = datas[3]
                try:
                    msg = await bot.get_messages(username, msgid)
                    await bot.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                except UsernameNotOccupied:
                    await bot.send_message(message.chat.id, f"**The username is not occupied by anyone**", reply_to_message_id=message.id)
                except Exception as e:
                    await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

            # wait time
            time.sleep(3)

# handle private
async def handle_private(message: pyrogram.types.messages_and_media.message.Message, chatid: int, msgid: int):
    try:
        msg = await bot.get_messages(chatid, msgid)
        msg_type = get_message_type(msg)

        if "Text" == msg_type:
            await bot.send_message(message.chat.id, msg.text, entities=msg.entities, reply_to_message_id=message.id)
            return

        smsg = await bot.send_message(message.chat.id, '__Downloading__', reply_to_message_id=message.id)
        active_downloads[message.chat.id] = True  # بدء التحميل
        dosta = threading.Thread(target=lambda: downstatus(f'{message.id}downstatus.txt', smsg), daemon=True)
        dosta.start()
        file = await bot.download_media(msg, progress=progress, progress_args=[message, "down"])
        os.remove(f'{message.id}downstatus.txt')

        if not active_downloads.get(message.chat.id, True):  # التحقق من إيقاف التحميل
            await bot.send_message(message.chat.id, "**تم إيقاف التحميل.**", reply_to_message_id=message.id)
            return

        upsta = threading.Thread(target=lambda: upstatus(f'{message.id}upstatus.txt', smsg), daemon=True)
        upsta.start()
        active_uploads[message.chat.id] = True  # بدء الرفع

        if "Document" == msg_type:
            try:
                thumb = await bot.download_media(msg.document.thumbs[0].file_id)
            except:
                thumb = None
            await bot.send_document(message.chat.id, file, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
            if thumb is not None: os.remove(thumb)

        elif "Video" == msg_type:
            # استخدام الصورة المصغرة الافتراضية
            thumb = DEFAULT_THUMBNAIL

            # إرسال الفيديو مع الصورة المصغرة
            await bot.send_video(message.chat.id, file, duration=msg.video.duration, width=msg.video.width, height=msg.video.height, thumb=thumb, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])

        elif "Animation" == msg_type:
            await bot.send_animation(message.chat.id, file, reply_to_message_id=message.id)

        elif "Sticker" == msg_type:
            await bot.send_sticker(message.chat.id, file, reply_to_message_id=message.id)

        elif "Voice" == msg_type:
            await bot.send_voice(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])

        elif "Audio" == msg_type:
            try:
                thumb = await bot.download_media(msg.audio.thumbs[0].file_id)
            except:
                thumb = None
            await bot.send_audio(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id, progress=progress, progress_args=[message, "up"])
            if thumb is not None: os.remove(thumb)

        elif "Photo" == msg_type:
            await bot.send_photo(message.chat.id, file, caption=msg.caption, caption_entities=msg.caption_entities, reply_to_message_id=message.id)

        os.remove(file)
        if os.path.exists(f'{message.id}upstatus.txt'): os.remove(f'{message.id}upstatus.txt')
        await bot.delete_messages(message.chat.id, [smsg.id])

    except Exception as e:
        await bot.send_message(message.chat.id, f"**Error** : __{e}__", reply_to_message_id=message.id)

# get the type of message
def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except: pass

    try:
        msg.video.file_id
        return "Video"
    except: pass

    try:
        msg.animation.file_id
        return "Animation"
    except: pass

    try:
        msg.sticker.file_id
        return "Sticker"
    except: pass

    try:
        msg.voice.file_id
        return "Voice"
    except: pass

    try:
        msg.audio.file_id
        return "Audio"
    except: pass

    try:
        msg.photo.file_id
        return "Photo"
    except: pass

    try:
        msg.text
        return "Text"
    except: pass

USAGE = """
OWNER :@X_XF8

**الأوامر المتاحة:**
- /start: بدء استخدام البوت.

"""

# بدء تشغيل البوت
if __name__ == "__main__":
    bot.run()
