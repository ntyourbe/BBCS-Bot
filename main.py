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

# ================== MENU ==================
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🔍 Cari")
    keyboard.add("ℹ️ Bantuan", "📢 Channel")
    return keyboard

# ================== FORCE JOIN ==================
GROUPS = [
    {
        "id": -1003759776336,
        "name": "BBCS REBORN",
        "link": "https://t.me/+XBiM2t3a6-JlMzk1"
    },
    {
        "id": -1003883822593,
        "name": "DONGHUA SUB INDO",
        "link": "https://t.me/+5Jy_jkyvPqQ1YTU1"
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

# ================== ANTI FLOOD ==================
last_user = {}
FLOOD_DELAY = 2

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

# ================== START ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if not is_user_joined(user_id):
        keyboard = types.InlineKeyboardMarkup(row_width=1)

        for group in GROUPS:
            keyboard.add(
                types.InlineKeyboardButton(
                    f"Join {group['name']}",
                    url=group["link"]
                )
            )

        keyboard.add(
            types.InlineKeyboardButton("✅ SAYA SUDAH JOIN", callback_data="cek_join")
        )

        bot.send_message(
            message.chat.id,
            "<b>Halo Braderkuu 👋</b>\n\n"
            "Kamu wajib join grup di bawah ini dulu sebelum menggunakan bot 👇",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        return

    bot.send_message(
        message.chat.id,
        "*Halo Braderkuu* 👋\n"
        "Ketik *ID* video untuk mencari",
        parse_mode="Markdown"
        reply_markup=main_menu()
    )

# ================== CEK JOIN ==================
@bot.callback_query_handler(func=lambda call: call.data == "cek_join")
def cek_join(call):
    if is_user_joined(call.from_user.id):
        bot.edit_message_text(
            "✅ Verifikasi berhasil!\nSekarang kamu bisa menggunakan bot 🎉\n Ketik ID Video untuk mencari..",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "❌ Masih belum join semua grup!", show_alert=True)

# ================== CEK ID GRUP / CHANNEL ==================
@bot.message_handler(commands=['id'])
def cek_id(message):
    chat = message.chat
    teks = (
        f"🆔 <b>INFO CHAT</b>\n\n"
        f"Nama : {chat.title}\n"
        f"ID : <code>{chat.id}</code>\n"
        f"Tipe : {chat.type}"
    )

    bot.reply_to(message, teks, parse_mode="HTML")

# ================= MENU ===================== 
@bot.message_handler(func=lambda m: m.text == "🔍 Cari")
def menu_cari(message):
    bot.send_message(
        message.chat.id,
        "🔎 Silakan ketik *ID* video yang ingin dicari",
        parse_mode="Markdown"
    )
    
@bot.message_handler(func=lambda m: m.text == "ℹ️ Bantuan")
def menu_bantuan(message):
    bot.send_message(
        message.chat.id,
        "ℹ️ *Panduan*\n\n"
        "- Join grup dulu\n"
        "- Ketik ID video\n"
        "- Bot akan menampilkan hasil",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "📢 Channel")
def menu_channel(message):
    bot.send_message(
        message.chat.id,
        "📢 Channel resmi:\nhttps://t.me/xxxxx",
        disable_web_page_preview=True
    )

# ================== SEARCH ==================
@bot.message_handler(func=lambda message: True)
def auto_search(message):
    user_id = message.from_user.id
    now = time.time()

    if not is_user_joined(user_id):
        bot.reply_to(message, "🚫 Join grup dulu, klik /start")
        return

    if user_id in last_user and now - last_user[user_id] < FLOOD_DELAY:
        return

    last_user[user_id] = now

    query = message.text.lower().strip()

    if not data_cache:
        bot.reply_to(message, "⏳ Data masih dimuat...")
        return

    hasil = [i for i in data_cache if query in i.get("judul", "").lower()]

    if not hasil:
        bot.reply_to(message, "❌ Data tidak ditemukan")
        return

    for item in hasil[:10]:
        judul = item.get("judul", "Tanpa Judul")
        link = item.get("link", "#")
        gambar = item.get("gambar")  # 🔥 TAMBAHAN

        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("BUKA LINK", url=link)
        )

        # ====== KIRIM GAMBAR JIKA ADA ======
        if gambar:
            bot.send_photo(
                message.chat.id,
                photo=gambar,
                caption=f"ID : <b>{judul}</b>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        else:
            bot.send_message(
                message.chat.id,
                f"ID : <b>{judul}</b>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
# ================== RUN ==================
print("Bot berjalan...")
bot.remove_webhook()
time.sleep(2)
bot.infinity_polling(skip_pending=True)
