import asyncio
import html
import random

from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import API_HASH, API_ID, NEW_REQ_MODE, UPDATE_CHANNEL, SUPPORT_GROUP, BOT_BRAND, ADMINS
from plugins.database import db

QUOTES = [
    "⚡ Automate the boring work. Let your bot handle the queue.",
    "🚀 Fast approvals. Clean controls. Useful statistics.",
    "🛡️ Keep your community organized with simple automation.",
    "📊 Every accepted request is counted in your dashboard.",
    "✨ Add once, configure once, let Synax handle the requests.",
]


def link(username):
    return f"https://t.me/{username.lstrip('@')}"


def main_kb(username):
    u = username.lstrip("@")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{u}?startgroup=true"),
         InlineKeyboardButton("📢 Add to Channel", url=f"https://t.me/{u}?startchannel=true")],
        [InlineKeyboardButton("❓ Help & Support", callback_data="help"),
         InlineKeyboardButton("📊 My Stats", callback_data="mystats")],
        [InlineKeyboardButton("💬 Quote", callback_data="quote"),
         InlineKeyboardButton("📖 Guide", callback_data="guide")],
        [InlineKeyboardButton("📢 Updates", url=link(UPDATE_CHANNEL)),
         InlineKeyboardButton("🆘 Support", url=link(SUPPORT_GROUP))],
    ])


def back_home():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Home", callback_data="home")]])


HELP_TEXT = f"""<blockquote><b>📘 Synax Join Manager — Help Center</b></blockquote>

<b>➕ Add to Group</b>
Tap <b>Add to Group</b>, select your group and make the bot an administrator.

<b>📢 Add to Channel</b>
Tap <b>Add to Channel</b>, select your channel and make the bot an administrator.

<b>⚙️ Required permission</b>
The bot needs permission to <b>invite/add users</b> so Telegram can allow it to approve join requests.

<b>⚡ Automatic mode</b>
When Auto Approval is enabled, new join requests are approved as they arrive.

<b>📨 Old pending requests</b>
Use <code>/login</code> to connect an admin account, then <code>/accept</code> and forward a message from the target chat. This is for older pending requests.

<b>🔐 Login flow</b>
<code>/login</code> → phone number → Telegram OTP → 2FA password if enabled.
Never share your OTP or password with anyone.

<b>🧾 Commands</b>
<code>/start</code> • Home
<code>/help</code> • Help Center
<code>/stats</code> • Approval statistics
<code>/quote</code> • Random quote
<code>/login</code> • Connect account for old requests
<code>/logout</code> • Remove saved session
<code>/accept</code> • Process old pending requests
<code>/admin</code> • Admin Control Center

<blockquote>📢 Updates: {UPDATE_CHANNEL}  •  🆘 Support: {SUPPORT_GROUP}</blockquote>"""


GUIDE_TEXT = """<blockquote><b>🚀 Quick Setup Guide</b></blockquote>

<b>Step 1</b> — Tap <b>➕ Add to Group</b> or <b>📢 Add to Channel</b>.

<b>Step 2</b> — Select your target chat.

<b>Step 3</b> — Promote the bot to administrator and allow the required invite/manage permission.

<b>Step 4</b> — Make sure the chat is configured to accept join requests.

<b>Step 5</b> — New requests will be approved automatically when Auto Approval is ON.

<b>Step 6</b> — Open <code>/stats</code> to see accepted requests and managed chats.

<b>Old requests?</b> Use <code>/login</code>, then <code>/accept</code> and forward a message from the target chat.
"""


async def ensure_user(c, m):
    if not m.from_user:
        return
    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id, m.from_user.first_name)


@Client.on_message(filters.command("start"))
async def start_message(c, m):
    await ensure_user(c, m)
    me = await c.get_me()
    name = html.escape(m.from_user.first_name or "there")
    text = f"""<blockquote><b>✨ Welcome to {html.escape(BOT_BRAND)}</b></blockquote>
Hello <b>{name}</b> 👋

<b>Advanced Telegram Join Request Manager</b>

<blockquote>⚡ Add me to your Group/Channel → make me admin → I can automatically handle incoming join requests.</blockquote>

<b>Features</b>
• ⚡ Automatic join-request approval
• 📊 Accepted-user statistics
• 📢 Group & Channel support
• 📨 Old pending-request processor
• 💬 Quote & Help Center
• 🛡️ Admin-only Control Center

<b>Choose what you want to do:</b>"""
    await m.reply_text(text, reply_markup=main_kb(me.username), disable_web_page_preview=True)


@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(c, m):
    await ensure_user(c, m)
    await m.reply_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Setup Guide", callback_data="guide")],
        [InlineKeyboardButton("📢 Updates", url=link(UPDATE_CHANNEL)), InlineKeyboardButton("🆘 Support", url=link(SUPPORT_GROUP))],
        [InlineKeyboardButton("⬅️ Home", callback_data="home")],
    ]))


async def stats_text():
    total = await db.total_accepted()
    chats = await db.chat_count()
    users = await db.total_users_count()
    return f"""<blockquote><b>📊 Approval Statistics</b></blockquote>
<b>👥 Accepted:</b> <code>{total:,}</code>
<b>📢 Managed chats:</b> <code>{chats:,}</code>
<b>🤖 Bot users:</b> <code>{users:,}</code>

<blockquote>Each successful approval is recorded in the database.</blockquote>"""


@Client.on_message(filters.command("stats") & filters.private)
async def stats_cmd(c, m):
    await ensure_user(c, m)
    await m.reply_text(await stats_text(), reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="mystats"), InlineKeyboardButton("⬅️ Home", callback_data="home")]
    ]))


@Client.on_message(filters.command("quote") & filters.private)
async def quote_cmd(c, m):
    await m.reply_text(f"<blockquote><b>💬 Quote of the Moment</b></blockquote>\n{random.choice(QUOTES)}",
                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 New Quote", callback_data="quote"), InlineKeyboardButton("⬅️ Home", callback_data="home")]]))


async def quote_message(q):
    await q.message.edit_text(f"<blockquote><b>💬 Quote of the Moment</b></blockquote>\n{random.choice(QUOTES)}",
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 New Quote", callback_data="quote"), InlineKeyboardButton("⬅️ Home", callback_data="home")]]))


@Client.on_callback_query(filters.regex("^quote$"))
async def quote_cb(c, q):
    await quote_message(q)
    await q.answer("Fresh quote ✨")


@Client.on_callback_query(filters.regex("^help$"))
async def help_cb(c, q):
    await q.message.edit_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Setup Guide", callback_data="guide")],
        [InlineKeyboardButton("📢 Updates", url=link(UPDATE_CHANNEL)), InlineKeyboardButton("🆘 Support", url=link(SUPPORT_GROUP))],
        [InlineKeyboardButton("⬅️ Home", callback_data="home")],
    ]))
    await q.answer()


@Client.on_callback_query(filters.regex("^guide$"))
async def guide_cb(c, q):
    await q.message.edit_text(GUIDE_TEXT, reply_markup=back_home())
    await q.answer()


@Client.on_callback_query(filters.regex("^mystats$"))
async def stats_cb(c, q):
    await q.answer()
    await q.message.edit_text(await stats_text(), reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="mystats"), InlineKeyboardButton("⬅️ Home", callback_data="home")]
    ]))


@Client.on_callback_query(filters.regex("^home$"))
async def home_cb(c, q):
    me = await c.get_me()
    await q.message.edit_text(f"""<blockquote><b>✨ {html.escape(BOT_BRAND)}</b></blockquote>
<b>Advanced Join Request Manager</b>

Add me to a Group or Channel as administrator and use the controls below.

<blockquote>⚡ Automatic approvals • 📊 Live stats • 📨 Old requests • 🛡️ Admin controls</blockquote>""", reply_markup=main_kb(me.username))
    await q.answer()


@Client.on_chat_join_request()
async def approve_new(client, request):
    enabled = await db.get_setting("auto_mode", NEW_REQ_MODE)
    if not enabled:
        return
    try:
        await client.approve_chat_join_request(request.chat.id, request.from_user.id)
        await db.add_user(request.from_user.id, request.from_user.first_name)
        await db.record_accept(request.chat.id, request.chat.title, request.from_user.id)
        try:
            await client.send_message(request.from_user.id, f"<blockquote><b>🎉 Request Approved!</b></blockquote>\nWelcome to <b>{html.escape(request.chat.title or 'the chat')}</b> 👋")
        except Exception:
            pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        print("Join request error:", repr(e))


@Client.on_message(filters.command("accept") & filters.private)
async def accept(client, message):
    status = await message.reply_text("⏳ <b>Preparing old-request mode...</b>")
    session = await db.get_session(message.from_user.id)
    if not session:
        return await status.edit_text("⚠️ <b>Login required.</b> Use <code>/login</code> first.")

    acc = Client("synax_old_request_session", session_string=session, api_hash=API_HASH, api_id=API_ID)
    try:
        await acc.start()
    except Exception:
        return await status.edit_text("❌ Session expired. Use <code>/logout</code>, then <code>/login</code> again.")

    try:
        await status.edit_text("📨 <b>Forward a message from the target Group/Channel here.</b>\n\nYour logged-in account must be an administrator there.")
        forwarded = await client.ask(message.chat.id, "Forward the message now:", timeout=120)
        if not forwarded.forward_from_chat or forwarded.forward_from_chat.type in (enums.ChatType.PRIVATE, enums.ChatType.BOT):
            return await status.edit_text("❌ Please forward a message from a Group or Channel.")

        chat_id = forwarded.forward_from_chat.id
        try:
            await forwarded.delete()
        except Exception:
            pass

        chat = await acc.get_chat(chat_id)
        await status.edit_text("⚡ <b>Accepting pending requests...</b>")
        count = 0
        while True:
            batch = [r async for r in acc.get_chat_join_requests(chat_id, limit=100)]
            if not batch:
                break
            for req in batch:
                try:
                    await acc.approve_chat_join_request(chat_id, req.user.id)
                    if await db.record_accept(chat_id, chat.title, req.user.id):
                        count += 1
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    continue
            await asyncio.sleep(0.5)
        await status.edit_text(f"<blockquote><b>✅ Old Requests Completed</b></blockquote>\n\n👥 Newly accepted: <code>{count:,}</code>")
    except asyncio.TimeoutError:
        await status.edit_text("⌛ Timed out. Run <code>/accept</code> again.")
    except Exception as e:
        await status.edit_text(f"❌ <b>Could not process requests.</b>\n<code>{html.escape(str(e)[:500])}</code>")
    finally:
        try:
            await acc.stop()
        except Exception:
            pass
