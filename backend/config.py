# config.py
import os

DB_NAME = os.environ.get("DB_NAME", "mydb")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "mysecret")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "https://discord.com/api/webhooks/1371667263777800292/2oZhwkE0x-0dEfMKG0MQGulVcAgXdzBDRlSzIxsKybf_6jGex5dSFzduru3BPKe9tu9D")
