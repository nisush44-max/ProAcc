from os import environ

API_ID = int(environ.get("API_ID", "37502609"))
API_HASH = environ.get("API_HASH", "cd4e39a4344aad8946b904292abbdf14")
BOT_TOKEN = environ.get("BOT_TOKEN", "")
DB_URI = environ.get("DB_URI", "mongodb+srv://synaxbots:synaxbotsalways#123@cluster0.nessphe.mongodb.net/?appName=Cluster0")
DB_NAME = environ.get("DB_NAME", "synax_join_manager")
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "-1003835007743")) if environ.get("LOG_CHANNEL", "-1003835007743").lstrip("-").isdigit() else 0


def _admins():
    raw = environ.get("ADMINS", "8363262755")
    return {int(x.strip()) for x in raw.replace(";", ",").split(",") if x.strip().lstrip("-").isdigit()}


ADMINS = _admins()
NEW_REQ_MODE = environ.get("NEW_REQ_MODE", "true").lower() in {"1", "true", "yes", "on"}
UPDATE_CHANNEL = environ.get("UPDATE_CHANNEL", "@synaxBotz")
SUPPORT_GROUP = environ.get("SUPPORT_GROUP", "@SynaxSupport")
BOT_BRAND = environ.get("BOT_BRAND", "Synax Acceptor")
