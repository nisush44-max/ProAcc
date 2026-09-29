import asyncio
import time

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMINS, NEW_REQ_MODE
from plugins.database import db


def is_admin(uid):
    return int(uid) in ADMINS


async def panel_text():
    auto = await db.get_setting("auto_mode", NEW_REQ_MODE)
    total = await db.total_accepted()
    chats = await db.chat_count()
    users = await db.total_users_count()
    return f"""<blockquote><b>🛡️ SYNAX ADMIN CONTROL CENTER</b></blockquote>
<b>System:</b> 🟢 Online
<b>Auto Approval:</b> {'🟢 ON' if auto else '🔴 OFF'}
<b>Accepted Requests:</b> <code>{total:,}</code>
<b>Managed Chats:</b> <code>{chats:,}</code>
<b>Bot Users:</b> <code>{users:,}</code>

<blockquote>Admin controls are visible only to configured administrators.</blockquote>"""


def panel_kb(auto):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Dashboard", callback_data="admin_stats"), InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🟢 Auto ON" if auto else "🔴 Auto OFF", callback_data="admin_toggle"), InlineKeyboardButton("📋 Chats", callback_data="admin_chats")],
        [InlineKeyboardButton("👥 Users", callback_data="admin_users"), InlineKeyboardButton("🔄 Refresh", callback_data="admin_panel")],
        [InlineKeyboardButton("❌ Close", callback_data="admin_close")],
    ])


@Client.on_message(filters.command(["admin", "panel"]) & filters.private)
async def admin_cmd(c, m):
    if not is_admin(m.from_user.id):
        return
    auto = await db.get_setting("auto_mode", NEW_REQ_MODE)
    await m.reply_text(await panel_text(), reply_markup=panel_kb(auto))


@Client.on_callback_query(filters.regex("^admin_"))
async def admin_cb(c, q):
    if not is_admin(q.from_user.id):
        return await q.answer("⛔ Admin only.", show_alert=True)

    action = q.data
    if action == "admin_close":
        try:
            await q.message.delete()
        except Exception:
            await q.answer("Already closed")
            return
        return await q.answer()

    if action == "admin_panel":
        auto = await db.get_setting("auto_mode", NEW_REQ_MODE)
        await q.message.edit_text(await panel_text(), reply_markup=panel_kb(auto))
        return await q.answer("Refreshed")

    if action == "admin_toggle":
        current = await db.get_setting("auto_mode", NEW_REQ_MODE)
        new_value = not current
        await db.set_setting("auto_mode", new_value)
        await q.message.edit_text(await panel_text(), reply_markup=panel_kb(new_value))
        return await q.answer("Auto approval updated")

    if action == "admin_stats":
        await q.message.edit_text(await panel_text(), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Panel", callback_data="admin_panel")]]))
        return await q.answer()

    if action == "admin_chats":
        rows = await db.get_chats(25)
        lines = ["<blockquote><b>📋 MANAGED CHATS</b></blockquote>"]
        if not rows:
            lines.append("No accepted requests have been recorded yet.")
        else:
            for i, row in enumerate(rows, 1):
                title = str(row.get("title", "Unknown")).replace("<", "&lt;").replace(">", "&gt;")
                lines.append(f"<b>{i}. {title}</b> — <code>{int(row.get('accepted', 0)):,}</code> accepted")
        await q.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Panel", callback_data="admin_panel")]]))
        return await q.answer()

    if action == "admin_users":
        users = await db.total_users_count()
        await q.message.edit_text(f"<blockquote><b>👥 USER DATABASE</b></blockquote>\n<b>Total bot users:</b> <code>{users:,}</code>\n\nUse <code>/broadcast</code> as a reply to the message you want to send.",
                                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"), InlineKeyboardButton("⬅️ Panel", callback_data="admin_panel")]]))
        return await q.answer()

    if action == "admin_broadcast":
        await q.message.edit_text("<blockquote><b>📢 BROADCAST CENTER</b></blockquote>\n\nReply to any message with <code>/broadcast</code>.\nThe bot will show live progress and success/failed/removed counts.",
                                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Panel", callback_data="admin_panel")]]))
        return await q.answer("Broadcast instructions opened")


async def broadcast_one(bot, uid, msg):
    try:
        await msg.copy(uid)
        return "success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_one(bot, uid, msg)
    except (InputUserDeactivated, UserIsBlocked, PeerIdInvalid):
        await db.delete_user(uid)
        return "removed"
    except Exception:
        return "failed"


@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast(c, m):
    if not is_admin(m.from_user.id) or not m.reply_to_message:
        return

    total = await db.total_users_count()
    users = await db.get_all_users()
    done = success = removed = failed = 0
    status = await m.reply_text("📢 <b>Broadcast started...</b>")
    started = time.monotonic()

    async for user in users:
        done += 1
        result = await broadcast_one(c, user["id"], m.reply_to_message)
        if result == "success":
            success += 1
        elif result == "removed":
            removed += 1
        else:
            failed += 1
        if done % 20 == 0 or done == total:
            try:
                await status.edit_text(f"<blockquote><b>📡 BROADCAST LIVE</b></blockquote>\n<b>Total:</b> <code>{total:,}</code>\n<b>Completed:</b> <code>{done:,}/{total:,}</code>\n<b>Success:</b> <code>{success:,}</code>\n<b>Removed:</b> <code>{removed:,}</code>\n<b>Failed:</b> <code>{failed:,}</code>")
            except Exception:
                pass

    elapsed = int(time.monotonic() - started)
    await status.edit_text(f"<blockquote><b>✅ BROADCAST COMPLETE</b></blockquote>\n<b>Time:</b> <code>{elapsed}s</code>\n<b>Total:</b> <code>{total:,}</code>\n<b>Completed:</b> <code>{done:,}</code>\n<b>Success:</b> <code>{success:,}</code>\n<b>Removed:</b> <code>{removed:,}</code>\n<b>Failed:</b> <code>{failed:,}</code>")
