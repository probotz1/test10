import time
import math
import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.enums import ParseMode

PROGRESS = """
• {0} of {1}
• Speed: {2}
• ETA: {3}
"""

async def progress_for_pyrogram(current, total, ud_type, message, start, client: Client):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff)
        time_to_completion = round((total - current) / speed)
        estimated_total_time = elapsed_time + time_to_completion
        elapsed_time = TimeFormatter(seconds=elapsed_time)
        estimated_total_time = TimeFormatter(seconds=estimated_total_time)
        progress = "[{0}{1}]".format(
            ''.join(["⬢" for i in range(math.floor(percentage / 10))]),
            ''.join(["⬡" for i in range(10 - math.floor(percentage / 10))])
        )
        tmp = progress + PROGRESS.format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed) + "/s",
            estimated_total_time if estimated_total_time != '' else "Calculating"
        )
        try:
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.id,
                text="{}\n{}".format(
                    ud_type,
                    tmp
                ),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("JOIN", url='https://t.me/ATXBOTSi')]]),
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(5)

def humanbytes(size):
    """ Humanize size """
    if not size:
        return ""
    power = 1024
    n = 0
    power_dict = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return "{:.2f} {}B".format(size, power_dict[n])


def TimeFormatter(seconds: float) -> str:
    """ Humanize time """
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]
