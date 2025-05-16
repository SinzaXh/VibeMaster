import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputStream, AudioPiped
import youtube_dl
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")
OWNER_USERNAME = os.getenv("OWNER_USERNAME")
BOT_USERNAME = os.getenv("BOT_USERNAME")

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client(name="userbot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
pytgcalls = PyTgCalls(user)

queue = []

def yt_search(query):
    with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            return info['url'], info['title'], info['thumbnail'], info['webpage_url']
        except Exception as e:
            return None, None, None, None

@app.on_message(filters.command("start"))
async def start_command(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me to Group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📚 Help", callback_data="help")]
    ])
    await message.reply_text("I'm a Music Bot! Add me to your group to play music.", reply_markup=buttons)

@app.on_callback_query(filters.regex("help"))
async def help_callback(client, callback_query):
    help_text = """**Available Commands:**
/play [song name or URL] - Play a song
/vplay [song name or URL] - Play video
/pause - Pause song
/resume - Resume song
/skip - Skip song
/stop - Stop and clear queue
"""
    await callback_query.message.edit_text(help_text)

@app.on_message(filters.command(["play", "vplay"]))
async def play_command(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: /play [song name or URL]")

    query = " ".join(message.command[1:])
    url, title, thumb, yt_url = yt_search(query)
    if not url:
        return await message.reply_text("Failed to find audio.")

    audio = AudioPiped(url)
    queue.append(audio)

    if not pytgcalls.active_calls:
        await pytgcalls.join_group_call(message.chat.id, audio)
        await message.reply_photo(
            photo=thumb,
            caption=f"▶️ Now Playing: [{title}]({yt_url})",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏸ Pause", callback_data="pause"),
                InlineKeyboardButton("▶️ Resume", callback_data="resume"),
                InlineKeyboardButton("⏭ Skip", callback_data="skip"),
                InlineKeyboardButton("⏹ Stop", callback_data="stop")
            ]])
        )
    else:
        await message.reply_text(f"Queued: {title}")

@app.on_callback_query(filters.regex("pause"))
async def pause(client, callback_query):
    await pytgcalls.pause_stream(callback_query.message.chat.id)
    await callback_query.answer("Paused")

@app.on_callback_query(filters.regex("resume"))
async def resume(client, callback_query):
    await pytgcalls.resume_stream(callback_query.message.chat.id)
    await callback_query.answer("Resumed")

@app.on_callback_query(filters.regex("skip"))
async def skip(client, callback_query):
    chat_id = callback_query.message.chat.id
    if len(queue) > 1:
        queue.pop(0)
        await pytgcalls.change_stream(chat_id, queue[0])
        await callback_query.answer("Skipped")
    else:
        await pytgcalls.leave_group_call(chat_id)
        queue.clear()
        await callback_query.answer("Queue ended")

@app.on_callback_query(filters.regex("stop"))
async def stop(client, callback_query):
    await pytgcalls.leave_group_call(callback_query.message.chat.id)
    queue.clear()
    await callback_query.answer("Stopped")

async def main():
    await app.start()
    await user.start()
    await pytgcalls.start()
    print("Bot is running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
