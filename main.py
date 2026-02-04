import telebot
import requests
import csv
from io import StringIO
import os
import time
import threading

TOKEN = os.getenv("TOKEN")
SHEET_CSV_URL = os.getenv("SHEET_CSV_URL")
bot = telebot.TeleBot(TOKEN)


if not TOKEN:
    raise ValueError("TOKEN tidak terbaca")
if not SHEET_CSV_URL:
    raise ValueError("SHEET_CSV_URL tidak terbaca")

# ================== CACHE ==================
data_cache = []

def update_sheet():
    global data_cache
    while True:
        try:
            print("Mengambil data dari Database...")
            response = requests.get(SHEET_CSV_URL, timeout=10)
            f = StringIO(response.text)
            reader = csv.DictReader(f)
            data_cache = list(reader)
            print("Database diperbarui")
        except Exception as e:
            print("Gagal ambil database:", e)

        time.sleep(300)  # 5 menit

threading.Thread(target=update_sheet, daemon=True).start()

# ================== BOT ==================

@bot.message_handler(commands=['start'])
def start(message):
    teks = """
*Halo Braderkuu* 👋
Selamat datang di Bot Pencarian *BBCS Reborn*
Cukup Ketik *ID* video disini

Contoh:
_1234_
"""
    bot.reply_to(message, teks, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def auto_search(message):
    query = message.text.lower().strip()

    if not data_cache:
        bot.reply_to(message, "Data masih dimuat, coba lagi beberapa detik.")
        return

    hasil = []
    for item in data_cache:
        if query in item['judul'].lower():
            hasil.append(item)

    if not hasil:
        bot.reply_to(message, "Data tidak ditemukan.")
        return

    for item in hasil:
        teks = f"<b>{item['judul']}</b>\n<a href='{item['link']}'>Buka Link</a>"
        bot.send_message(message.chat.id, teks, parse_mode="HTML")

bot.infinity_polling()
