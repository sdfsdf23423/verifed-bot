import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from unixgram import Bot
from db import init_db, check_code, verify_user, is_verified, unverify_user

BOT_TOKEN = "3193529251:YwHD3tqh47Wd7hs7Ru2mHDoaME5puZxQ"
bot = Bot(BOT_TOKEN)
init_db()

def say(cid, text, parse_mode=None):
    try:
        bot.send_message(cid, text, parse_mode=parse_mode)
    except Exception as e:
        print(f"[!] send error: {e}", flush=True)

@bot.message_handler()
def handle(message):
    text = (message.text or "").strip()
    cid = message.chat.id
    chat_type = getattr(message.chat, "type", "private")

    from_user = getattr(message, "from_user", None) or getattr(message, "from", None)
    if from_user and getattr(from_user, "is_bot", False):
        return

    uid = None
    uname = ""
    if from_user:
        uid = getattr(from_user, "id", None)
        uname = getattr(from_user, "username", "") or ""

    if chat_type == "private":
        if text.startswith("/"):
            cmd = text.split()[0].lstrip("/").split("@")[0].lower()

            if cmd == "verify":
                if not uid:
                    say(cid, "Ошибка: не удалось определить пользователя.")
                    return

                if is_verified(uid):
                    say(cid, "✅ Твой аккаунт уже привязан!")
                    return

                parts = text.split(maxsplit=1)
                if len(parts) < 2 or not parts[1].strip():
                    say(cid,
                        "🔑 <b>Верификация</b>\n\n"
                        "1. Зайди на сайт и получи код\n"
                        "2. Напиши: <code>/verify КОД ПАРОЛЬ</code>\n\n"
                        "Пример: <code>/verify ABC123 mypass123</code>",
                        parse_mode="HTML"
                    )
                    return

                args = parts[1].strip().split()
                if len(args) < 2:
                    say(cid, "❌ Формат: <code>/verify КОД ПАРОЛЬ</code>", parse_mode="HTML")
                    return

                code = args[0].upper()
                password = args[1]
                result = check_code(code)
                if result and result["username"].lower() == uname.lower():
                    verify_user(uid, uname, password)
                    say(cid,
                        f"✅ Аккаунт @{uname} привязан!\n\n"
                        f"🔑 Твой пароль: <code>{password}</code>\n"
                        f"⚠️ Запиши его — он нужен для входа на сайт.",
                        parse_mode="HTML"
                    )
                else:
                    say(cid, "❌ Неверный код или username не совпадает.\nПроверь на сайте и попробуй снова.")
                return

            if cmd == "status":
                if uid and is_verified(uid):
                    say(cid, f"✅ @{uname} — верифицирован")
                else:
                    say(cid, "❌ Ты не верифицирован.\nИспользуй /verify чтобы привязать аккаунт.")
                return

            if cmd == "unverify":
                if uid and is_verified(uid):
                    unverify_user(uid)
                    say(cid, f"🔓 Аккаунт @{uname} отвязан.")
                else:
                    say(cid, "❌ Ты не привязан.")
                return

            if cmd == "help":
                say(cid,
                    "🔑 <b>Verify Bot</b>\n\n"
                    "<code>/verify КОД ПАРОЛЬ</code> — привязать аккаунт\n"
                    "<code>/unverify</code> — отвязать аккаунт\n"
                    "<code>/status</code> — проверить статус\n"
                    "<code>/help</code> — эта справка",
                    parse_mode="HTML"
                )
                return

        say(cid, "Напиши /help для списка команд.")

try:
    bot.set_my_commands([
        {"command": "verify", "description": "привязать аккаунт"},
        {"command": "status", "description": "проверить статус"},
        {"command": "help", "description": "справка"},
    ])
except Exception:
    pass

while True:
    try:
        print("verify bot запущен…", flush=True)
        bot.polling()
    except KeyboardInterrupt:
        break
    except Exception as e:
        print("обрыв:", e, flush=True)
        time.sleep(5)
