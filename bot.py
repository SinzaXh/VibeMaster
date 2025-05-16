import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pytgcalls import PyTgCalls, idle
from pytgcalls.types.input_stream import InputStream, AudioPiped
from yt_dlp import YoutubeDL

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")
OWNER_USERNAME = os.getenv("OWNER_USERNAME")
BOT_USERNAME = os.getenv("BOT_USERNAME")

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
pytgcalls = PyTgCalls(user)

queue = []

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': True,
    'quiet': True,
    'extract_flat': 'in_playlist'
}

def get_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Play", callback_data="play")],
        [InlineKeyboardButton("⏸ Pause", callback_data="pause"),
         InlineKeyboardButton("⏭ Skip", callback_data="skip")],
        [InlineKeyboardButton("⏹ Stop", callback_data="stop")],
        [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]
    ])

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        f"Hi {message.from_user.first_name}!\nI'm your music bot.",
        reply_markup=get_buttons()
    )

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    await message.reply_text(
        "/play [song name or URL] - Play song\n"
        "/pause - Pause\n"
        "/resume - Resume\n"
        "/skip - Skip current\n"
        "/stop - Stop and clear queue"
    )

@app.on_message(filters.command("play"))
async def play(client, message: Message):
    query = " ".join(message.command[1:])
    if not query:
        return await message.reply("Please provide a song name or YouTube URL.")
    
    with YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(query, download=False)
        url = info['url']
        title = info.get("title", "Unknown Title")

    await pytgcalls.join_group_call(
        message.chat.id,
        AudioPiped(url)
    )
    await message.reply(f"Playing: {title}", reply_markup=get_buttons())

@app.on_message(filters.command("pause"))
async def pause(_, message: Message):
    await pytgcalls.pause_stream(message.chat.id)
    await message.reply("Paused", reply_markup=get_buttons())

@app.on_message(filters.command("resume"))
async def resume(_, message: Message):
    await pytgcalls.resume_stream(message.chat.id)
    await message.reply("Resumed", reply_markup=get_buttons())

@app.on_message(filters.command("skip"))
async def skip(_, message: Message):
    await message.reply("Skipping not implemented in this version.", reply_markup=get_buttons())

@app.on_message(filters.command("stop"))
async def stop(_, message: Message):
    await pytgcalls.leave_group_call(message.chat.id)
    await message.reply("Stopped.", reply_markup=get_buttons())

async def main():
    await app.start()
    await user.start()
    await pytgcalls.start()
    print("Bot is running!")
    await idle()
    await app.stop()
    await user.stop()

if __name__ == "__main__":
    asyncio.run(main())
