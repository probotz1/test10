import os
import time
import math
import subprocess
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

# Function to run ffmpeg commands
def run_ffmpeg(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr.decode()}")

# Function to download media with progress updates
async def download_media(client, message, path):
    start_time = time.time()
    size = message.video.file_size if message.video else message.audio.file_size
    progress = lambda current, total: progress_callback(current, total, message, start_time)
    file_path = await client.download_media(message, path, progress=progress)
    return file_path

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
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Please specify the start and end times in seconds (e.g., /trim_video 10 30).")
        return

    try:
        start_time = int(args[1])
        end_time = int(args[2])
        if start_time >= end_time:
            await message.reply("End time must be greater than start time.")
            return

        await message.reply("Please send the video you want to trim.")

        @app.on_message(filters.video)
        async def trim_video(client, video_message: Message):
            video_file = await download_media(client, video_message, DOWNLOADS_DIR)
            output_file = os.path.join(DOWNLOADS_DIR, f"trimmed_{os.path.basename(video_file)}")

            try:
                cmd = [
                    "ffmpeg", "-i", video_file, "-ss", str(start_time), "-to", str(end_time),
                    "-c", "copy", output_file
                ]
                run_ffmpeg(cmd)
                await video_message.reply_video(output_file)
                os.remove(video_file)
                os.remove(output_file)
            except Exception as e:
                await video_message.reply(f"Error trimming video: {e}")
                os.remove(video_file)

    except ValueError:
        await message.reply("Please provide valid start and end times in seconds.")

# Command handler for '/remove_audio' command
@app.on_message(filters.command("remove_audio"))
async def remove_audio_command(client, message: Message):
    await message.reply("Send me a video to remove audio from.")

    @app.on_message(filters.video)
    async def remove_audio(client, video_message: Message):
        video_file = await download_media(client, video_message, DOWNLOADS_DIR)
        output_file = os.path.join(DOWNLOADS_DIR, f"no_audio_{os.path.basename(video_file)}")

        try:
            cmd = [
                "ffmpeg", "-i", video_file, "-c", "copy", "-an", output_file
            ]
            run_ffmpeg(cmd)
            await video_message.reply_video(output_file)
            os.remove(video_file)
            os.remove(output_file)
        except Exception as e:
            await video_message.reply(f"Error removing audio: {e}")
            os.remove(video_file)

# Command handler for '/merge_audio' command
@app.on_message(filters.command("merge_audio"))
async def merge_audio_command(client, message: Message):
    await message.reply("Send me the video whose audio you want to replace, followed by the new audio file.")

    @app.on_message(filters.video)
    async def video_received(client, video_message: Message):
        video_file = await download_media(client, video_message, DOWNLOADS_DIR)
        await video_message.reply("Now send me the audio file you want to merge with this video.")

        @app.on_message(filters.audio | filters.voice)
        async def audio_received(client, audio_message: Message):
            audio_file = await download_media(client, audio_message, DOWNLOADS_DIR)
            output_file = os.path.join(DOWNLOADS_DIR, f"merged_{os.path.basename(video_file)}")

            try:
                cmd = [
                    "ffmpeg", "-i", video_file, "-i", audio_file, "-c:v", "copy", "-map", "0:v:0",
                    "-map", "1:a:0", "-shortest", output_file
                ]
                run_ffmpeg(cmd)
                await video_message.reply_video(output_file)
                os.remove(video_file)
                os.remove(audio_file)
                os.remove(output_file)
            except Exception as e:
                await video_message.reply(f"Error merging audio: {e}")
                os.remove(video_file)
                os.remove(audio_file)

# Command handler for '/video_to_audio' command
@app.on_message(filters.command("video_to_audio"))
async def video_to_audio_command(client, message: Message):
    await message.reply("Send me a video to extract audio from.")

    @app.on_message(filters.video)
    async def extract_audio(client, video_message: Message):
        video_file = await download_media(client, video_message, DOWNLOADS_DIR)
        output_file = os.path.join(DOWNLOADS_DIR, f"{os.path.splitext(os.path.basename(video_file))[0]}.mp3")

        try:
            cmd = [
                "ffmpeg", "-i", video_file, "-q:a", "0", "-map", "a", output_file
            ]
            run_ffmpeg(cmd)
            await video_message.reply_audio(output_file)
            os.remove(video_file)
            os.remove(output_file)
        except Exception as e:
            await video_message.reply(f"Error extracting audio: {e}")
            os.remove(video_file)

if __name__ == "__main__":
    app.run()
