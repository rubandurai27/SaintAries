from telethon import Button

from aries import telethn as tbot
from aries.events import register

PHOTO = "https://telegra.ph/file/eb3bf6147ef96da2d31b5.jpg"


@register(pattern=("/alive|/ALIVE"))
async def awake(event):
    event.sender.first_name
    ARIES = "**Hello im VAATHI** \n\n"
    ARIES += "**ALL SYSTEM WORKING PROPERLY**\n\n"
    ARIES += " ☬ ⌊ **Python :** __3.9.7__ ⌉\n\n"
    ARIES += " ☬ ⌊ **Pyrogram :** __1.2.9__ ⌉\n\n"
    ARIES += " ☬ ⌊ **MongoDB :** __2.5.1__ ⌉\n\n"
    ARIES += " ☬ ⌊ **Platform :** __linux__ ⌉\n\n"
    ARIES += " ☬ ⌊ **My Lord** : [RUBANDURAI27](https://t.me/RUBANDURAI27) ☠⌉\n\n"
    ARIES += " ☬ ⌊ **Sαιητ λrιεs** ⌉\n\n"
    ARIES += " ☬ ⌊ **TELETHON : 6.6.6 Latest** ⌉\n\n"
    ARIES += " |||| || ||| |||| || |||||| ||||| || || ||"
    BUTTON = [
        [
            Button.url("Support", "https://t.me/POWERROCKERS"),
            Button.url("Updates", "https://t.me/TN_BOTZ"),
        ]
    ]
    await tbot.send_file(event.chat_id, PHOTO, caption=ARIES, buttons=BUTTON)


__mod_name__ = "Alive"
