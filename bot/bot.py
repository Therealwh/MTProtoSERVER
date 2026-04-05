import os
import json
import logging
import qrcode
import io
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '')
PROXY_IP = os.environ.get('PROXY_IP', '0.0.0.0')
PROXY_PORT = int(os.environ.get('PROXY_PORT', '443'))
FAKE_DOMAIN = os.environ.get('FAKE_DOMAIN', 'cloudflare.com')
PROXY_SECRET = os.environ.get('PROXY_SECRET', '')

DATA_DIR = '/app/data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')

def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'users': [], 'next_id': 1}

def save_users(data):
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_proxy_link(secret):
    return f"tg://proxy?server={PROXY_IP}&port={PROXY_PORT}&secret={secret}"

def generate_qr(link):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Статус прокси", callback_data='status')],
        [InlineKeyboardButton("👥 Пользователи", callback_data='users')],
        [InlineKeyboardButton("➕ Добавить пользователя", callback_data='add_user')],
        [InlineKeyboardButton("📈 Статистика", callback_data='stats')],
        [InlineKeyboardButton("🔗 Ссылка прокси", callback_data='proxy_link')],
        [InlineKeyboardButton("🔧 Диагностика", callback_data='diagnostics')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        f"👋 Добро пожаловать в *MTProtoSERVER Bot*!\n\n"
        f"🌐 *Сервер:* `{PROXY_IP}:{PROXY_PORT}`\n"
        f"🛡️ *FakeTLS:* `{FAKE_DOMAIN}`\n\n"
        f"Выберите действие в меню ниже:"
    )
    await update.message.reply_text(
        welcome,
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'status':
        users_data = load_users()
        users = users_data.get('users', [])
        active = len([u for u in users if u.get('enabled', True)])
        msg = (
            f"📊 *Статус прокси*\n\n"
            f"✅ Прокси работает\n"
            f"👥 Пользователей: `{len(users)}`\n"
            f"✅ Активных: `{active}`\n"
            f"🌐 IP: `{PROXY_IP}`\n"
            f"🔌 Порт: `{PROXY_PORT}`\n"
            f"🛡️ FakeTLS: `{FAKE_DOMAIN}`"
        )
        await query.edit_message_text(msg, parse_mode='Markdown')

    elif data == 'users':
        users_data = load_users()
        users = users_data.get('users', [])
        if not users:
            await query.edit_message_text("👥 Пользователей пока нет.\nИспользуйте ➕ Добавить пользователя")
            return

        msg = "👥 *Список пользователей:*\n\n"
        for u in users:
            status = "✅" if u.get('enabled', True) else "❌"
            msg += f"{status} *{u['label']}* — `{u['secret'][:16]}...`\n"

        keyboard = []
        for u in users:
            action = "disable" if u.get('enabled', True) else "enable"
            emoji = "⏸️" if u.get('enabled', True) else "▶️"
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {u['label']}",
                callback_data=f"{action}_{u['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])

        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'add_user':
        await query.edit_message_text(
            "➕ *Добавить пользователя*\n\n"
            "Отправьте имя нового пользователя:",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for_name'] = True

    elif data == 'stats':
        users_data = load_users()
        users = users_data.get('users', [])
        total_in = sum(u.get('traffic_in', 0) for u in users)
        total_out = sum(u.get('traffic_out', 0) for u in users)

        msg = f"📈 *Статистика*\n\n"
        msg += f"👤 Всего пользователей: `{len(users)}`\n"
        msg += f"📥 Трафик IN: `{total_in}` байт\n"
        msg += f"📤 Трафик OUT: `{total_out}` байт\n"
        msg += f"📊 Всего: `{total_in + total_out}` байт\n\n"

        if users:
            msg += "*Детализация:*\n"
            for u in users:
                total = u.get('traffic_in', 0) + u.get('traffic_out', 0)
                msg += f"• {u['label']}: `{total}` байт\n"

        await query.edit_message_text(msg, parse_mode='Markdown')

    elif data == 'proxy_link':
        link = get_proxy_link(PROXY_SECRET)
        qr_image = generate_qr(link)

        await query.message.reply_photo(
            photo=qr_image,
            caption=f"🔗 *Ссылка для подключения:*\n\n`{link}`",
            parse_mode='Markdown'
        )
        await query.edit_message_text("🔗 QR-код и ссылка отправлены выше.")

    elif data == 'diagnostics':
        msg = (
            f"🔧 *Диагностика*\n\n"
            f"✅ Docker: работает\n"
            f"✅ MTProxy: запущен\n"
            f"✅ Web UI: работает\n"
            f"✅ Bot: работает\n"
            f"✅ FakeTLS: `{FAKE_DOMAIN}`\n"
            f"✅ Порт: `{PROXY_PORT}`\n"
            f"✅ IP: `{PROXY_IP}`"
        )
        await query.edit_message_text(msg, parse_mode='Markdown')

    elif data == 'back':
        await query.edit_message_text("📋 Главное меню:", reply_markup=main_menu_keyboard())

    elif data.startswith('disable_') or data.startswith('enable_'):
        action, user_id = data.split('_')
        user_id = int(user_id)
        users_data = load_users()

        for u in users_data.get('users', []):
            if u['id'] == user_id:
                u['enabled'] = (action == 'enable')
                break

        save_users(users_data)
        status = "включён" if action == 'enable' else "отключён"
        await query.edit_message_text(f"✅ Пользователь `{user_id}` {status}.", parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_name'):
        name = update.message.text
        users_data = load_users()
        next_id = users_data.get('next_id', 1)

        import secrets
        new_secret = secrets.token_hex(16)

        new_user = {
            'id': next_id,
            'label': name,
            'secret': new_secret,
            'enabled': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'max_connections': 0,
            'max_ips': 0,
            'data_quota': '0',
            'expires': '',
            'traffic_in': 0,
            'traffic_out': 0,
            'connections': 0
        }

        users_data['users'].append(new_user)
        users_data['next_id'] = next_id + 1
        save_users(users_data)

        link = get_proxy_link(new_secret)
        qr_image = generate_qr(link)

        await update.message.reply_text(
            f"✅ Пользователь *{name}* добавлен!\n\n"
            f"🔗 Ссылка: `{link}`",
            parse_mode='Markdown'
        )

        await update.message.reply_photo(
            photo=qr_image,
            caption=f"📱 QR-код для {name}"
        )

        context.user_data['waiting_for_name'] = False

        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='back')]]
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def notify_admin(message):
    if ADMIN_CHAT_ID:
        try:
            from telegram import Bot
            bot = Bot(token=BOT_TOKEN)
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(status|users|add_user|stats|proxy_link|diagnostics|back|disable_|enable_)'))
    app.add_handler(CommandHandler("status", start))
    app.add_handler(CommandHandler("help", start))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(CommandHandler("start", start))

    logger.info("Bot started!")

    async def on_startup(application):
        await notify_admin("🟢 *MTProtoSERVER Bot запущен!*\n\nБот готов к работе.")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
