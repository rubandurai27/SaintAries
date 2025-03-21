import importlib
import re
import sys
import time
import datetime
from sys import argv
from typing import Optional, List

from pyrogram import filters
from telegram import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Message,
    ParseMode,
    Update,
    User,
    Bot,
)
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import run_async, DispatcherHandlerStop, Dispatcher
from telegram.utils.helpers import escape_markdown

from aries import (
    ALLOW_EXCL,
    BL_CHATS,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    WHITELIST_CHATS,
    StartTime,
    dispatcher,
    pbot,
    telethn,
    ubot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from aries.modules import ALL_MODULES
from aries.modules.helper_funcs.alternate import typing_action
from aries.modules.helper_funcs.chat_status import is_user_admin
from aries.modules.helper_funcs.misc import paginate_modules
from aries.modules.helper_funcs.readable_time import get_readable_time
from aries.modules.sql import users_sql as sql

HELP_MSG = "Click The Button Below To Get Help Menu In Your Private Message."
HELP_IMG = "https://telegra.ph/file/ac893610cae84f302b2da.jpg"
GROUP_START_IMG = (
    "CAACAgIAAx0CXBdkHQAC34lhpHKAV3nIlqfcnYmDkIhbOFTktwACFBAAAkXe2EuBs3crQ6mMdR4E"
)

PM_START_TEXT = """
Hello there, [👋](https://telegra.ph/file/ac893610cae84f302b2da.jpg) I'm {}.
Im Powerfull Management Bot And I Will Help In Managing Your Group.
𝐂𝐥𝐢𝐤𝐞 𝐁𝐞𝐥𝐨𝐰 𝐓𝐡𝐞 𝐁𝐮𝐭𝐭𝐨𝐧 𝐀𝐧𝐝 𝐆𝐞𝐭 𝐃𝐨𝐜𝐮𝐦𝐚𝐧𝐭𝐚𝐭𝐢𝐨𝐧 𝐎𝐟 𝐌𝐨𝐝𝐮𝐥𝐞𝐬..
Maintained by : [POWERROCKERS](https://t.me/POWERROCKERS)
Founder And Dev Of : [IDZEROID SYNDICATES](https://t.me/idzeroidsupport).
➖➖➖➖➖➖➖➖➖➖➖➖➖
• *Uptime:* `{}`
• `{}` *Users, across* `{}` *chats.*
➖➖➖➖➖➖➖➖➖➖➖➖➖
Made specifically to manage your group , I specialize in managing Entertainment and all type groups and channels.
✪ Make sure you read *DETAILS* Section Below ✪ 
"""

buttons = [
    [
        InlineKeyboardButton(text=" ｢ Details 」", callback_data="aboutmanu_"),
        InlineKeyboardButton(text=" ｢ Inline 」", switch_inline_query_current_chat=""),
    ],
    [
        InlineKeyboardButton(
            text=" ➕ ｢ ADD YOUR GROUP 」➕ ",
            url="t.me/idzeroid_bot?startgroup=true",
        ),
    ],
    [
        InlineKeyboardButton(text=" ｢ Support 」", url="http://t.me/POWERROCKERS"),
        InlineKeyboardButton(text=" [Close] ", callback_data="close"),
        InlineKeyboardButton(text=" ｢ Update 」", url="http://t.me/TNROCKERS2021"),
    ],
]


HELP_STRINGS = f"""
*Main Commands :* [VAATHI](https://telegra.ph/file/ac893610cae84f302b2da.jpg)
✪ /start: Starts me! You've probably already used this.
✪ /help: Click this, I'll let you know about myself!
✪ /donate: You can support my creater using this command.
✪ /settings: 
   ◔ in PM: will send you your settings for all supported modules.
   ◔ in a Group: will redirect you to pm, with all that chat's settings.
""".format(
    dispatcher.bot.first_name,
    "" if not ALLOW_EXCL else "\nAll commands can either be used with / or !.\n",
)


DONATE_STRING = """Hello, glad to hear you want to donate!
 You can support the project via [pulsa](#) or by contacting @IdzXartez\
 Supporting isnt always financial! \
 Those who cannot provide monetary support are welcome to help us develop the bot at ."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
USER_BOOK = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("aries.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "get_help") and imported_module.get_help:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__user_book__"):
        USER_BOOK.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard
    )


def test(update, context):
    try:
        print(update)
    except:
        pass
    update.effective_message.reply_text(
        "Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN
    )
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="⬅️ BACK", callback_data="help_back"
                                )
                            ]
                        ]
                    ),
                )
            elif args[0].lower() == "markdownhelp":
                IMPORTED["extras"].markdown_help_sender(update)
            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            message.reply_text(
                PM_START_TEXT.format(
                    escape_markdown(context.bot.first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats(),
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        message.reply_animation(
            GROUP_START_IMG,
            caption="<code> Aries Online \nI am Awake Since</code>: <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Support", url=f"https://telegram.dog/POWERROCKERS"
                        ),
                        InlineKeyboardButton(
                            text="Updates", url="https://telegram.dog/TNROCKERS2021"
                        ),
                    ],
                ]
            ),
        )


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "* ｢  Help  for  {}  module 」*\n".format(HELPABLE[module].__mod_name__)
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back", callback_data="help_back"
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                text="Support", url="https://t.me/idzeroidsupport"
                            ),
                        ],
                    ]
                ),
            )
        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()
    except Exception as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            query.message.edit_text(excp.message)
            LOGGER.exception("Exception in help buttons. %s", str(query.data))


def aries_about_callback(update, context):
    query = update.callback_query
    if query.data == "aboutmanu_":
        query.message.edit_text(
            text=f"*👋Hi again!  The name's {dispatcher.bot.first_name}  \n\nA powerful group management bot built to help you manage your group easily.* "
            f"\n\n 🔥 Join [Idzeroid Syndicates](https://t.me/idzeroidsupport) To Keep Yourself Updated About {dispatcher.bot.first_name} 🔥"
            f"\n\n I have the normal GROUP MANAGING functions like flood control, a warning system etc but I mainly have the advanced and handy Antispam system and the SIBYL banning system which safegaurds and helps your group from spammers."
            f"\n\n ⚡️ 》 I can restrict users."
            f"\n\n ⚡️ 》 I can greet users with customizable welcome messages and even set a group's rules."
            f"\n\n ⚡️ 》 I have an advanced anti-flood system."
            f"\n\n ⚡️ 》 I can warn users until they reach max warns, with each predefined actions such as ban, mute, kick, etc."
            f"\n\n ⚡️ 》 I have a note keeping system, blacklists, and even predetermined replies on certain keywords."
            f"\n\n ⚡️ 》 I check for admins' permissions before executing any command and more stuffs"
            f"\n\n If you have any question about *Aries*, let us know at @IdzeroidSupport."
            f"\n\n👇 You Can Know More About *Aries* By Clicking The Below Buttons 👇",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="How To Use Me", callback_data="aboutmanu_howto"
                        ),
                        InlineKeyboardButton(
                            text="T.A.C", callback_data="aboutmanu_tac"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="Help & Commands", callback_data="help_back"
                        )
                    ],
                    [InlineKeyboardButton(text="Back", callback_data="aboutmanu_back")],
                ]
            ),
        )
    elif query.data == "aboutmanu_back":
        query.message.edit_text(
            PM_START_TEXT.format(
                escape_markdown(context.bot.first_name),
                escape_markdown(get_readable_time((time.time() - StartTime))),
                sql.num_users(),
                sql.num_chats(),
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
        )

    elif query.data == "aboutmanu_howto":
        query.message.edit_text(
            text=f"* ｢ BASIC HELP 」*"
            f"\nIf You Can Also Add {dispatcher.bot.first_name} To Your Chats By Clicking [Here](http://t.me/{dispatcher.bot.username}?startgroup=true) And Selecting Chat. \n"
            f"\n\nYou Can get support {dispatcher.bot.first_name} by joining [support](https://t.me/idzeroidsupport).\n"
            f"",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Admins Settings", callback_data="aboutmanu_permis"
                        ),
                        InlineKeyboardButton(
                            text="Anti Spam", callback_data="aboutmanu_spamprot"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="Music Setup", callback_data="aboutmanu_cbguide"
                        ),
                    ],
                    [InlineKeyboardButton(text="Back", callback_data="aboutmanu_")],
                ]
            ),
        )
    elif query.data == "aboutmanu_credit":
        query.message.edit_text(
            text=f"*Aries Is the redisigned version of Daisy and Saitama And Othrer for the best performance.*"
            f"\n\nAries source code was rewritten by @IdzXartez and All Of Conrtibutor For Help Aries"
            f"\n\nIf Any Question About aries, \nLet Us Know At @Idzeroidsupport.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="aboutmanu_tac")]]
            ),
        )

    elif query.data == "aboutmanu_permis":
        query.message.edit_text(
            text=f"<b> ｢ Admin Permissions 」</b>"
            f"\nTo avoid slowing down, {dispatcher.bot.first_name} caches admin rights for each user. This cache lasts about 10 minutes; this may change in the future. This means that if you promote a user manually (without using the /promote command), {dispatcher.bot.first_name} will only find out ~10 minutes later."
            f"\n\nIF you want to update them immediately, you can use the /admincache command,thta'll force {dispatcher.bot.first_name} to check who the admins are again and their permissions"
            f"\n\nIf you are getting a message saying:"
            f"\n<Code>You must be this chat administrator to perform this action!</code>"
            f"\nThis has nothing to do with {dispatcher.bot.first_name}'s rights; this is all about YOUR permissions as an admin. {dispatcher.bot.first_name} respects admin permissions; if you do not have the Ban Users permission as a telegram admin, you won't be able to ban users with {dispatcher.bot.first_name}. Similarly, to change {dispatcher.bot.first_name} settings, you need to have the Change group info permission."
            f"\n\nThe message very clearly says that you need these rights - <i>not {dispatcher.bot.first_name}.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="aboutmanu_howto")]]
            ),
        )
    elif query.data == "aboutmanu_spamprot":
        query.message.edit_text(
            text="* ｢ Anti-Spam Settings 」*"
            "\n- /antispam <on/off/yes/no>: Change antispam security settings in the group, or return your current settings(when no arguments)."
            "\n_This helps protect you and your groups by removing spam flooders as quickly as possible._"
            "\n\n- /setflood <int/'no'/'off'>: enables or disables flood control"
            "\n- /setfloodmode <ban/kick/mute/tban/tmute> <value>: Action to perform when user have exceeded flood limit. ban/kick/mute/tmute/tban"
            "\n_Antiflood allows you to take action on users that send more than x messages in a row. Exceeding the set flood will result in restricting that user._"
            "\n\n- /addblacklist <triggers>: Add a trigger to the blacklist. Each line is considered one trigger, so using different lines will allow you to add multiple triggers."
            "\n- /blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>: Action to perform when someone sends blacklisted words."
            "\n_Blacklists are used to stop certain triggers from being said in a group. Any time the trigger is mentioned, the message will immediately be deleted. A good combo is sometimes to pair this up with warn filters!_"
            "\n\n- /reports <on/off>: Change report setting, or view current status."
            "\n • If done in pm, toggles your status."
            "\n • If in chat, toggles that chat's status."
            "\n_If someone in your group thinks someone needs reporting, they now have an easy way to call all admins._"
            "\n\n- /lock <type>: Lock items of a certain type (not available in private)"
            "\n- /locktypes: Lists all possible locktypes"
            "\n_The locks module allows you to lock away some common items in the telegram world; the bot will automatically delete them!_"
            '\n\n- /addwarn <keyword> <reply message>: Sets a warning filter on a certain keyword. If you want your keyword to be a sentence, encompass it with quotes, as such: /addwarn "very angry" This is an angry user. '
            "\n- /warn <userhandle>: Warns a user. After 3 warns, the user will be banned from the group. Can also be used as a reply."
            "\n- /strongwarn <on/yes/off/no>: If set to on, exceeding the warn limit will result in a ban. Else, will just kick."
            "\n_If you're looking for a way to automatically warn users when they say certain things, use the /addwarn command._"
            "\n\n- /welcomemute <off/soft/strong>: All users that join, get muted"
            "\n_ A button gets added to the welcome message for them to unmute themselves. This proves they aren't a bot! soft - restricts users ability to post media for 24 hours. strong - mutes on join until they prove they're not bots._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="aboutmanu_howto")]]
            ),
        )
    elif query.data == "aboutmanu_tac":
        query.message.edit_text(
            text=f"<b> ｢ Terms and Conditions 」</b>\n"
            f"\n<i>To Use This Bot, You Need To Read Terms and Conditions Carefully.</i>\n"
            f"\n✪ We always respect your privacy \n  We never log into bot's api and spying on you \n  We use a encripted database \n  Bot will automatically stops if someone logged in with api."
            f"\n✪ Always try to keep credits, so \n  This hardwork is done by @IdzXartez spending many sleepless nights.. So, Respect it."
            f"\n✪ Some modules in this bot is owned by different authors, So, \n  All credits goes to them \n  Also for <b>Paul Larson for Marie</b>."
            f"\n✪ If you need to ask anything about \n  this bot, Go @Idzeroidsupport."
            f"\n✪ If you asking nonsense in Support \n  Chat, you will get warned/banned."
            f"\n✪ All api's we used owned by originnal authors \n  Some api's we use Free version \n  Please don't overuse AI Chat."
            f"\n\nFor any kind of help, related to this bot, Join @idzeroidsupport."
            f"\n\n<i>Terms & Conditions will be changed anytime</i>\n",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Credits", callback_data="aboutmanu_credit"
                        ),
                        InlineKeyboardButton(text="Back", callback_data="aboutmanu_"),
                    ]
                ]
            ),
        )
    elif query.data == "aboutmanu_cbguide":
        query.message.edit_text(
            text=f"* ｢ How To Setup Music 」*\n"
            f"\n1. **first, add me to your group."
            f"\n2. **then promote me as admin and give all permissions except anonymous admin."
            f"\n3. **after promoting me, type /admincache in group to update the admin list."
            f"\n4. **add @IdzMusic to your group."
            f"\n5. **turn on the video chat first before start to play music.\n\n"
            f"\n📌 **if the userbot not joined to video chat, make sure if the video chat already turned on, or you can ask Admins in @idzeroidsupport.**\n"
            f"\n⚡ __Powered by Aries A.I__\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="[⇜]", callback_data="aboutmanu_cbhelps"
                        ),
                        InlineKeyboardButton(text="🔄", callback_data="aboutmanu_howto"),
                        InlineKeyboardButton(
                            text="[⇝]", callback_data="aboutmanu_cbhelps"
                        ),
                    ],
                ]
            ),
        )
    elif query.data == "aboutmanu_cbhelps":
        query.message.edit_text(
            text=f"* ｢ Music Command 」*\n"
            f"\n1. **/play (name song) for playing music."
            f"\n2. **/pause for paused music."
            f"\n3. **/resume for resume music."
            f"\n4. **/stop or /end for end music playing."
            f"\n5. **/music (name song) for download song."
            f"\n6. **/video (name video) for download video."
            f"\n7. **/lyrics for searching lyrics.\n\n"
            f"\n📌 **Also you can download music or video with push button menu.**\n"
            f"\n⚡ __Powered by Aries A.I__\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="[⇜]", callback_data="aboutmanu_cbguide"
                        ),
                        InlineKeyboardButton(text="🔄", callback_data="aboutmanu_howto"),
                        InlineKeyboardButton(
                            text="[⇝]", callback_data="aboutmanu_cbguide"
                        ),
                    ],
                ]
            ),
        )


@typing_action
def get_help(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.animation(
                HELP_IMG,
                HELP_MSG,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Help",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Support", url=f"https://telegram.dog/POWERROCKERS"
                        ),
                        InlineKeyboardButton(
                            text="Updates", url="https://telegram.dog/TNROCKERS2021"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="Music Setup", callback_data="aboutmanu_cbguide"
                        ),
                    ],
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


def settings_button(update, context):
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = context.bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = context.bot.get_chat(chat_id)
            query.message.edit_text(
                "Hi there! There are quite a few settings for *{}* - go ahead and pick what "
                "you're interested in.".format(chat.title),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = context.bot.get_chat(chat_id)
            query.message.edit_text(
                "Hi there! There are quite a few settings for *{}* - go ahead and pick what "
                "you're interested in.".format(chat.title),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = context.bot.get_chat(chat_id)
            query.message.edit_text(
                text="Hi there! There are quite a few settings for *{}* - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()
    except Exception as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            query.message.edit_text(excp.message)
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


def migrate_chats(update, context):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def is_chat_allowed(update, context):
    if len(WHITELIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id not in WHITELIST_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Unallowed chat! Leaving..."
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    if len(BL_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BL_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Unallowed chat! Leaving..."
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    if len(WHITELIST_CHATS) != 0 and len(BL_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BL_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Unallowed chat, leaving"
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    else:
        pass


def donate(update: Update, context: CallbackContext):
    update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
        update.effective_message.reply_text(
            "You can also donate to the person currently running me "
            "[here]({})".format(DONATION_LINK),
            parse_mode=ParseMode.MARKDOWN,
        )

    else:
        pass


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(f"@IdzeroidSupport", "⚡️")
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test, run_async=True)
    start_handler = CommandHandler("start", start, pass_args=True, run_async=True)

    help_handler = CommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(
        help_button, pattern=r"help_", run_async=True
    )

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_", run_async=True
    )

    about_callback_handler = CallbackQueryHandler(
        aries_about_callback, pattern=r"aboutmanu_", run_async=True
    )

    donate_handler = CommandHandler("donate", donate, run_async=True)

    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats, run_async=True
    )
    is_chat_allowed_handler = MessageHandler(
        Filters.chat_type.groups, is_chat_allowed, run_async=True
    )

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(is_chat_allowed_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)
            client.run_until_disconnected()

    else:
        LOGGER.info("Arie using long polling.")
        updater.start_polling(
            timeout=15,
            read_latency=4,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


try:
    ubot.start()
except BaseException:
    print("Userbot Error! Have you added a STRING_SESSION in deploying??")
    sys.exit(1)

if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
