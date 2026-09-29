import asyncio

from pyrogram import Client, filters
from pyrogram.errors import (
    PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid
)
from pyrogram.types import Message

from config import API_ID, API_HASH
from plugins.database import db

SESSION_STRING_SIZE = 300


@Client.on_message(filters.private & filters.command("logout"))
async def logout(client, message: Message):
    if await db.get_session(message.from_user.id) is None:
        return await message.reply_text("ℹ️ You are not logged in.")
    await db.set_session(message.from_user.id, None)
    await message.reply_text("✅ <b>Logged out successfully.</b>")


@Client.on_message(filters.private & filters.command("login"))
async def login(bot: Client, message: Message):
    if await db.get_session(message.from_user.id):
        return await message.reply_text("⚠️ You are already logged in. Use <code>/logout</code> first.")

    user_id = message.from_user.id
    phone_msg = await bot.ask(user_id, "📱 <b>Send your phone number with country code.</b>\nExample: <code>+919876543210</code>\n\nSend <code>/cancel</code> to stop.", timeout=300)
    if not phone_msg.text or phone_msg.text.strip() == "/cancel":
        return await phone_msg.reply_text("❌ Login cancelled.")

    phone = phone_msg.text.strip()
    account = Client("synax_login_session", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    try:
        await account.connect()
        sent = await account.send_code(phone)
        code_msg = await bot.ask(user_id, "🔐 <b>Enter the Telegram OTP.</b>\nExample: <code>1 2 3 4 5</code>\n\nSend <code>/cancel</code> to stop.", timeout=600)
        if not code_msg.text or code_msg.text.strip() == "/cancel":
            return await code_msg.reply_text("❌ Login cancelled.")
        code = code_msg.text.replace(" ", "").strip()

        try:
            await account.sign_in(phone, sent.phone_code_hash, code)
        except SessionPasswordNeeded:
            password_msg = await bot.ask(user_id, "🔒 <b>Two-step verification is enabled.</b> Send your 2FA password.\n\nSend <code>/cancel</code> to stop.", timeout=300)
            if not password_msg.text or password_msg.text.strip() == "/cancel":
                return await password_msg.reply_text("❌ Login cancelled.")
            try:
                await account.check_password(password_msg.text)
            except PasswordHashInvalid:
                return await password_msg.reply_text("❌ Invalid 2FA password.")

        session = await account.export_session_string()
        if len(session) < SESSION_STRING_SIZE:
            return await message.reply_text("❌ Could not create a valid session string.")
        await db.set_session(user_id, session)
        await message.reply_text("<blockquote><b>✅ Account Login Successful</b></blockquote>\nYou can now use <code>/accept</code> for old pending join requests.")
    except PhoneNumberInvalid:
        await message.reply_text("❌ Invalid phone number.")
    except PhoneCodeInvalid:
        await message.reply_text("❌ Invalid OTP.")
    except PhoneCodeExpired:
        await message.reply_text("⌛ OTP expired. Please run <code>/login</code> again.")
    except Exception as e:
        await message.reply_text(f"❌ <b>Login error:</b> <code>{str(e)[:500]}</code>")
    finally:
        try:
            await account.disconnect()
        except Exception:
            pass
