"""
MIT License

Copyright (c) 2021 TheHamkerCat

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import re
from pyrogram import filters
from misskaty import app
from misskaty.core.decorator.errors import capture_err
from misskaty.core.decorator.permissions import adminsOnly
from misskaty.core.keyboard import ikb
from database.filters_db import (
    delete_filter,
    get_filter,
    get_filters_names,
    save_filter,
)
from misskaty.helper.functions import extract_text_and_keyb

__MODULE__ = "Filters"
__HELP__ = """/filters To Get All The Filters In The Chat.
/addfilter [FILTER_NAME] To Save A Filter (Can be a sticker or text).
/stopfilter [FILTER_NAME] To Stop A Filter.

You can use markdown or html to save text too.
"""


@app.on_message(filters.command("addfilter") & ~filters.private)
@adminsOnly("can_change_info")
async def save_filters(_, message):
    if len(message.command) == 1 or not message.reply_to_message:
        return await message.reply_text("**Usage:**\nReply to a text or sticker with /filter [FILTER_NAME] to save it.")
    if not message.reply_to_message.text and not message.reply_to_message.sticker:
        return await message.reply_text("__**You can only save text or stickers in filters for now.**__")
    name = message.text.split(None, 1)[1].strip()
    if not name:
        return await message.reply_text("**Usage:**\n__/filter [FILTER_NAME]__")
    chat_id = message.chat.id
    _type = "text" if message.reply_to_message.text else "sticker"
    _filter = {
        "type": _type,
        "data": message.reply_to_message.text.markdown if _type == "text" else message.reply_to_message.sticker.file_id,
    }
    await save_filter(chat_id, name, _filter)
    await message.reply(f"__**Saved filter {name}.**__")


@app.on_message(filters.command("filters") & ~filters.private)
@capture_err
async def get_filterss(_, message):
    _filters = await get_filters_names(message.chat.id)
    if not _filters:
        return await message.reply_text("**No filters in this chat.**")
    _filters.sort()
    msg = f"List of filters in {message.chat.title} - {message.chat.id}\n"
    for _filter in _filters:
        msg += f"**-** `{_filter}`\n"
    await message.reply_text(msg)


@app.on_message(filters.command("stopfilter") & ~filters.private)
@adminsOnly("can_change_info")
async def del_filter(_, message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:**\n__/stop [FILTER_NAME]__")
    name = message.text.split(None, 1)[1].strip()
    if not name:
        return await message.reply_text("**Usage:**\n__/stop [FILTER_NAME]__")
    chat_id = message.chat.id
    deleted = await delete_filter(chat_id, name)
    if deleted:
        await message.reply_text(f"**Deleted filter {name}.**")
    else:
        await message.reply_text("**No such filter.**")


@app.on_message(
    filters.text & ~filters.private & ~filters.via_bot & ~filters.forwarded,
    group=2,
)
@capture_err
async def filters_re(_, message):
    text = message.text.lower().strip()
    if not text:
        return
    chat_id = message.chat.id
    list_of_filters = await get_filters_names(chat_id)
    for word in list_of_filters:
        pattern = r"( |^|[^\w])" + re.escape(word) + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            _filter = await get_filter(chat_id, word)
            data_type = _filter["type"]
            data = _filter["data"]
            if data_type == "text":
                keyb = None
                if re.findall(r"\[.+\,.+\]", data):
                    if keyboard := extract_text_and_keyb(ikb, data):
                        data, keyb = keyboard

                if message.reply_to_message:
                    await message.reply_to_message.reply(
                        data,
                        reply_markup=keyb,
                        disable_web_page_preview=True,
                    )

                    if text.startswith("~"):
                        await message.delete()
                    return

                return await message.reply(
                    data,
                    reply_markup=keyb,
                    quote=True,
                    disable_web_page_preview=True,
                )
            if message.reply_to_message:
                await message.reply_to_message.reply_sticker(data)

                if text.startswith("~"):
                    await message.delete()
                return
            await message.reply_sticker(data, quote=True)
