# Synax Join Manager — Advanced

Advanced Telegram Group/Channel join-request manager with automatic approval, old pending-request processing, statistics, broadcast and admin controls.

## Environment variables

- `API_ID` — Telegram API ID
- `API_HASH` — Telegram API hash
- `BOT_TOKEN` — BotFather token
- `DB_URI` — MongoDB URI
- `DB_NAME` — MongoDB database name (optional)
- `ADMINS` — comma-separated Telegram user IDs
- `NEW_REQ_MODE` — `true`/`false` default auto approval
- `UPDATE_CHANNEL` — default `@synaxBotz`
- `SUPPORT_GROUP` — default `@SynaxSupport`
- `BOT_BRAND` — default `Synax Join Manager`
- `LOG_CHANNEL` — optional numeric chat ID

## Run

```bash
pip install -r requirements.txt
python bot.py
```

For Render/other web-service hosts, the included `app.py` exposes a simple health endpoint.

## Important

1. Add the bot to the target group/channel as an administrator.
2. Give the bot the permission required to manage/invite users and approve join requests.
3. Put your Telegram user ID in `ADMINS` for the admin panel.
4. `/login` stores a Telegram user session in MongoDB. Use it only on a server you control and never share OTP/2FA credentials.
