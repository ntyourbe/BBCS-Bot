import telebot
from telebot import types
import requests
import csv
from io import StringIO
import os
import time
import threading


# ================== ENV ==================
TOKEN = os.getenv("BOT_TOKEN")
SHEET_CSV_URL = os.getenv("SHEET_CSV_URL")

if not TOKEN or not SHEET_CSV_URL:
    raise ValueError("BOT_TOKEN atau SHEET_CSV_URL belum diset di Environment Variables")

bot = telebot.TeleBot(TOKEN)


# ================== FORCE JOIN ==================
GROUPS = [
    {
        "id": -1003759776336,  # GANTI DENGAN ID GRUP KAMU
        "name": "BBCS REBORN",
        "link": "https://t.me/+XBiM2t3a6-JlMzk1"
    }
]


def is_user_joined(user_id):
    for group in GROUPS:
        try:
            member = bot.get_chat_member(group["id"], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True


# ================== CACHE ==================
data_cache = []

# ================== ANTI SPAM ==================
last_user = {}
FLOOD_DELAY = 2  # detik


def update_sheet():
    global data_cache
    while True:
        try:
            print("Mengambil data dari Google Sheet...")
            response = requests.get(SHEET_CSV_URL, timeout=15)
            response.raise_for_status()

            f = StringIO(response.text)
            reader = csv.DictReader(f)
            data_cache = list(reader)

            print(f"Database diperbarui ({len(data_cache)} data)")
        except Exception as e:
            print("Gagal ambil database:", e)

        time.sleep(300)


threading.Thread(target=update_sheet, daemon=True).start()

# ================== BOT ==================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if not is_user_joined(user_id):
        teks = (
            "🚫 <b>Akses Ditolak</b>\n\n"
            "Selamat datang di Bot Pencarian <b>BBCS Reborn</b>\n\n"
            "Kamu wajib join grup di bawah ini dulu sebelum menggunakan bot 👇\n\n"
            "Setelah join, klik tombol <b>✅ Saya sudah join</b>"
        )

        keyboard = types.InlineKeyboardMarkup(row_width=1)

        for group in GROUPS:
            keyboard.add(
                types.InlineKeyboardButton(
                    f"Join {group['name']}",
                    url=group["link"]
                )
            )

        keyboard.add(
            types.InlineKeyboardButton(
                "✅ Saya sudah join",
                callback_data="cek_join"
            )
        )

        bot.send_message(
            message.chat.id,
            teks,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    teks = (
        "*Halo Braderkuu* 👋\n"
        "Selamat datang di Bot Pencarian *BBCS Reborn*\n\n"
        "Cukup ketik *ID* video di sini\n\n"
        "Contoh:\n"
        "_1234_"
    )

    bot.send_message(
        message.chat.id,
        teks,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


@bot.callback_query_handler(func=lambda call: call.data == "cek_join")
def cek_join(call):
    user_id = call.from_user.id

    if is_user_joined(user_id):
        bot.edit_message_text(
            "✅ Verifikasi berhasil!\n\nSekarang kamu bisa menggunakan bot 🎉\n\n"
            "Silakan ketik *ID* video.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Kamu belum join semua grup!",
            show_alert=True
        )


@bot.message_handler(func=lambda message: True)
def auto_search(message):
    user_id = message.from_user.id

    if not is_user_joined(user_id):
        bot.reply_to(
            message,
            "🚫 Kamu belum join grup.\nGunakan /start untuk join dulu."
        )
        return

    uid = message.from_user.id
    now = time.time()

    # === ANTI FLOOD ===
    if uid in last_user and now - last_user[uid] < FLOOD_DELAY:
        return

    last_user[uid] = now
    # ==================

    query = message.text.lower().strip()

    if not data_cache:
        bot.reply_to(message, "😋 Data masih dimuat, coba lagi sebentar.")
        return

    hasil = []
    for item in data_cache:
        if query in item.get('judul', '').lower():
            hasil.append(item)

    if not hasil:
        bot.reply_to(message, "😭 Data tidak ditemukan.")
        return

    for item in hasil[:10]:
        judul = item.get('judul', 'Tanpa Judul')
        link = item.get('link', '#')

        teks = f"ID : <b>{judul}</b>"

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("BUKA LINK", url=link)
        )

        bot.send_message(
            message.chat.id,
            teks,
            parse_mode="HTML",
            reply_markup=keyboard
        )


# ================== RUN ==================
print("Bot berjalan...")
bot.infinity_polling(skip_pending=True)
