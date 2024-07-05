import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from moviepy.editor import VideoFileClip, AudioFileClip
import config
from progress import progress_for_pyrogram

# Initialize Pyrogram Client
app = Client("my_bot", api_id=config.api_id, api_hash=config.api_hash, bot_token=config.bot_token)

# State variables
user_state = {}

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Video Trimmer", callback_data="video_trimmer")],
        [InlineKeyboardButton("Audio Remover", callback_data="audio_remover")],
        [InlineKeyboardButton("Audio Replacer", callback_data="audio_replacer")],
        [InlineKeyboardButton("Video to Audio", callback_data="video_to_audio")],
    ])
    await message.reply("Choose an option:", reply_markup=keyboard)

@app.on_message(filters.command("help"))
async def help(client, message: Message):
    await message.reply("Send me a video or audio file, and I can trim, remove audio, replace audio, or extract audio.")

@app.on_callback_query()
async def handle_callback_query(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    user_state[user_id] = data
    if data == "video_trimmer":
        await callback_query.message.reply("Send me a video to trim.")
    elif data == "audio_remover":
        await callback_query.message.reply("Send me a video to remove audio from.")
    elif data == "audio_replacer":
        await callback_query.message.reply("Send me the video whose audio you want to replace, followed by the new audio file.")
    elif data == "video_to_audio":
        await callback_query.message.reply("Send me a video to extract audio from.")

@app.on_message(filters.video)
async def handle_video(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_state:
        await message.reply("Please select an option first.")
        return
    
    action = user_state[user_id]
    video = message.video
    file_path = await client.download_media(video, progress=progress_for_pyrogram, progress_args=("Downloading...", message, time.time(), client))
    
    if action == "video_trimmer":
        await message.reply("Please specify the start and end times in seconds (e.g., 10 30).")
        user_state[user_id] = ("trimming", file_path)
    
    elif action == "audio_remover":
        await message.reply("Removing audio...")
        clip = VideoFileClip(file_path)
        clip = clip.without_audio()
        output_path = "no_audio_video.mp4"
        clip.write_videofile(output_path)
        await client.send_video(message.chat.id, output_path, progress=progress_for_pyrogram, progress_args=("Uploading...", message, time.time(), client))
        os.remove(file_path)
        os.remove(output_path)
    
    elif action == "audio_replacer":
        await message.reply("Send me the new audio file.")
        user_state[user_id] = ("replacing", file_path)
    
    elif action == "video_to_audio":
        await message.reply("Extracting audio...")
        clip = VideoFileClip(file_path)
        output_path = "extracted_audio.mp3"
        clip.audio.write_audiofile(output_path)
        await client.send_audio(message.chat.id, output_path, progress=progress_for_pyrogram, progress_args=("Uploading...", message, time.time(), client))
        os.remove(file_path)
        os.remove(output_path)

@app.on_message(filters.audio)
async def handle_audio(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_state or not isinstance(user_state[user_id], tuple):
        await message.reply("Please select an option first.")
        return
    
    action, video_path = user_state[user_id]
    if action == "replacing":
        audio = message.audio
        audio_path = await client.download_media(audio, progress=progress_for_pyrogram, progress_args=("Downloading...", message, time.time(), client))
        
        await message.reply("Replacing audio...")
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        new_video_clip = video_clip.set_audio(audio_clip)
        output_path = "replaced_audio_video.mp4"
        new_video_clip.write_videofile(output_path)
        
        await client.send_video(message.chat.id, output_path, progress=progress_for_pyrogram, progress_args=("Uploading...", message, time.time(), client))
        os.remove(video_path)
        os.remove(audio_path)
        os.remove(output_path)
        del user_state[user_id]

@app.on_message(filters.text)
async def handle_text(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_state and isinstance(user_state[user_id], tuple):
        action, file_path = user_state[user_id]
        if action == "trimming":
            try:
                start, end = map(int, message.text.split())
                await message.reply("Trimming video...")
                clip = VideoFileClip(file_path).subclip(start, end)
                output_path = "trimmed_video.mp4"
                clip.write_videofile(output_path)
                await client.send_video(message.chat.id, output_path, progress=progress_for_pyrogram, progress_args=("Uploading...", message, time.time(), client))
                os.remove(file_path)
                os.remove(output_path)
                del user_state[user_id]
            except ValueError:
                await message.reply("Invalid format. Please specify the start and end times in seconds (e.g., 10 30).")

if __name__ == "__main__":
    app.run()
