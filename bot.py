import os
import time
import math
import subprocess
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from pyrogram.errors import MessageNotModified
from config import BOT_TOKEN, API_ID, API_HASH

# Initialize Pyrogram client
app = Client("my_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Directory for storing downloaded files
DOWNLOADS_DIR = "downloads"

# Ensure the downloads directory exists
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

# Progress template for status updates
PROGRESS_TEMPLATE = """
Progress: {0}%
Downloaded: {1} / {2}
Speed: {3}/s
ETA: {4}
"""

# Dictionary to store the last update time for each message
last_update_time = {}

# Function to display human-readable file size
def human_readable_size(size):
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

# Function to format time duration
def time_formatter(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    time_str = ((f"{days}d, " if days else "") +
                (f"{hours}h, " if hours else "") +
                (f"{minutes}m, " if minutes else "") +
                (f"{seconds}s, " if seconds else ""))
    return time_str.strip(', ')

# Progress callback function to update progress during downloads and uploads
async def progress_callback(current, total, message, start_time):
    now = time.time()
    elapsed_time = now - start_time
    if elapsed_time == 0:
        elapsed_time = 1  # Avoid division by zero

    speed = current / elapsed_time
    percentage = current * 100 / total
    eta = (total - current) / speed

    progress_str = "[{0}{1}]".format(
        ''.join(["⬢" for _ in range(math.floor(percentage / 10))]),
        ''.join(["⬡" for _ in range(10 - math.floor(percentage / 10))])
    )
    tmp = progress_str + PROGRESS_TEMPLATE.format(
        round(percentage, 2),
        human_readable_size(current),
        human_readable_size(total),
        human_readable_size(speed),
        time_formatter(eta)
    )

    # Throttle updates to every 10 seconds
    message_id = message.message_id
    if message_id not in last_update_time or (now - last_update_time[message_id]) > 10:
        try:
            await message.edit(
                text=tmp,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Owner", url='https://t.me/atxbots')]]
                )
            )
            last_update_time[message_id] = now
        except MessageNotModified:
            pass
        except Exception as e:
            print(f"Error updating progress: {e}")

# Command handler for '/start' command
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    welcome_text = (
        "Hello! I am your Bot.\n\n"
        "I can help you with audio and video tasks.\n\n"
        "To use me, send me a video or audio file and choose an option."
    )
    await message.reply(welcome_text)

# Command handler for '/help' command
@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/trim_video - Trim a video\n"
        "/remove_audio - Remove audio from a video\n"
        "/merge_audio - Merge audio with a video\n"
        "/video_to_audio - Extract audio from a video\n"
    )
    await message.reply(help_text)

# Command handler for '/trim_video' command
@app.on_message(filters.command("trim_video"))
async def trim_video_command(client, message: Message):
    await message.reply("Please specify the start and end times in seconds (e.g., 10 30).")

# Command handler for '/remove_audio' command
@app.on_message(filters.command("remove_audio"))
async def remove_audio_command(client, message: Message):
    await message.reply("Send me a video to remove audio from.")

# Command handler for '/merge_audio' command
@app.on_message(filters.command("merge_audio"))
async def merge_audio_command(client, message: Message):
    await message.reply("Send me the video whose audio you want to replace, followed by the new audio file.")

# Command handler for '/video_to_audio' command
@app.on_message(filters.command("video_to_audio"))
async def video_to_audio_command(client, message: Message):
    await message.reply("Send me a video to extract audio from.")

# Message handler for videos
@app.on_message(filters.video)
async def handle_video(client, message: Message):
    # Implement logic to handle various video processing tasks based on user state
    pass

# Callback query handler for interactive options
@app.on_callback_query()
async def handle_callback_query(client, query: CallbackQuery):
    # Implement callback query handling for interactive options
    pass

if __name__ == "__main__":
    app.run()
