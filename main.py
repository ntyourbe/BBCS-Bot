import telebot
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

# ================== CACHE ==================
data_cache = []

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

        time.sleep(300)  # update tiap 5 menit

threading.Thread(target=update_sheet, daemon=True).start()

# ================== BOT ==================

@bot.message_handler(commands=['start'])
def start(message):
    teks = (
        "*Halo Braderkuu* 👋\n"
        "Selamat datang di Bot Pencarian *BBCS Reborn*\n\n"
        "Cukup ketik *ID / Judul* video di sini\n\n"
        "Contoh:\n"
        "_1234_"
    )
    bot.reply_to(message, teks, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def auto_search(message):
    query = message.text.lower().strip()

    if not data_cache:
        bot.reply_to(message, "⏳ Data masih dimuat, coba lagi sebentar.")
        return

    hasil = []
    for item in data_cache:
        if query in item.get('judul', '').lower():
            hasil.append(item)

    if not hasil:
        bot.reply_to(message, "❌ Data tidak ditemukan.")
        return

    for item in hasil[:10]:  # batasi 10 hasil biar aman
        teks = (
            f"<b>{item.get('judul','Tanpa Judul')}</b>\n"
            f"<a href='{item.get('link','#')}'>Buka Link</a>"
        )
        bot.send_message(message.chat.id, teks, parse_mode="HTML")

# ================== RUN ==================
print("Bot berjalan...")
bot.infinity_polling(skip_pending=True)
