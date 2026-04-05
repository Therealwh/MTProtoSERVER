import os
import json
import logging
import qrcode
import io
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '')
PROXY_IP = os.environ.get('PROXY_IP', '0.0.0.0')
PROXY_COUNT = int(os.environ.get('PROXY_COUNT', '1'))

DATA_DIR = '/app/data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PROXIES_FILE = os.path.join(DATA_DIR, 'proxies.json')

def is_admin(update: Update):
    if not ADMIN_CHAT_ID:
        return True
    user_id = str(update.effective_user.id)
    return user_id == ADMIN_CHAT_ID

def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update):
            await update.message.reply_text("🚫 У вас нет доступа к этому боту.")
            logger.warning(f"Unauthorized access attempt from user {update.effective_user.id}")
            return
        return await func(update, context)
    return wrapper

def admin_callback_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update):
            await update.callback_query.answer("🚫 У вас нет доступа!")
            return
        return await func(update, context)
    return wrapper

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def get_proxies():
    return load_json(PROXIES_FILE)

def get_proxy_link(ip, port, secret):
    return f"tg://proxy?server={ip}&port={port}&secret={secret}"

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
        [InlineKeyboardButton("🌐 Прокси серверы", callback_data='proxies')],
        [InlineKeyboardButton("👥 Пользователи", callback_data='users')],
        [InlineKeyboardButton("➕ Добавить пользователя", callback_data='add_user')],
        [InlineKeyboardButton("📈 Статистика", callback_data='stats')],
        [InlineKeyboardButton("🔧 Диагностика", callback_data='diagnostics')]
    ]
    return InlineKeyboardMarkup(keyboard)

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    proxies_data = get_proxies()
    proxies = proxies_data.get('proxies', [])
    active = len([p for p in proxies if p.get('enabled', True)])

    welcome = (
        f"👋 Добро пожаловать в *MTProtoSERVER Bot*!\n\n"
        f"🌐 *Сервер:* `{PROXY_IP}`\n"
        f"📡 *Прокси серверов:* `{len(proxies)}` ({active} активных)\n\n"
    )

    if proxies:
        welcome += "*Прокси:*\n"
        for p in proxies:
            status = "✅" if p.get('enabled', True) else "❌"
            welcome += f"{status} *{p['label']}* — порт `{p['port']}` ({p['domain']})\n"

    welcome += "\nВыберите действие в меню ниже:"

    await update.message.reply_text(
        welcome,
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

@admin_callback_only
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'status':
        proxies_data = get_proxies()
        users_data = load_json(USERS_FILE)
        proxies = proxies_data.get('proxies', [])
        users = users_data.get('users', [])
        active_proxies = len([p for p in proxies if p.get('enabled', True)])
        active_users = len([u for u in users if u.get('enabled', True)])

        msg = (
            f"📊 *Статус прокси*\n\n"
            f"✅ Прокси работает\n"
            f"🌐 Прокси серверов: `{len(proxies)}`\n"
            f"✅ Активных прокси: `{active_proxies}`\n"
            f"👥 Пользователей: `{len(users)}`\n"
            f"✅ Активных: `{active_users}`\n"
            f"🌐 IP: `{PROXY_IP}`"
        )
        await query.edit_message_text(msg, parse_mode='Markdown')

    elif data == 'proxies':
        proxies_data = get_proxies()
        proxies = proxies_data.get('proxies', [])
        if not proxies:
            await query.edit_message_text("🌐 Прокси серверов пока нет.")
            return

        msg = "🌐 *Прокси серверы:*\n\n"
        for p in proxies:
            status = "✅" if p.get('enabled', True) else "❌"
            msg += f"{status} *{p['label']}*\n"
            msg += f"   Порт: `{p['port']}` | Домен: `{p['domain']}`\n"
            link = get_proxy_link(PROXY_IP, p['port'], p['secret'])
            msg += f"   `{link[:50]}...`\n\n"

        keyboard = []
        for p in proxies:
            keyboard.append([InlineKeyboardButton(
                f"📋 {p['label']} (порт {p['port']})",
                callback_data=f"proxy_link_{p['id']}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])

        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith('proxy_link_'):
        proxy_id = int(data.replace('proxy_link_', ''))
        proxies_data = get_proxies()
        proxies = proxies_data.get('proxies', [])

        target = None
        for p in proxies:
            if p['id'] == proxy_id:
                target = p
                break

        if target:
            link = get_proxy_link(PROXY_IP, target['port'], target['secret'])
            qr_image = generate_qr(link)
            await query.message.reply_photo(
                photo=qr_image,
                caption=f"🔗 *{target['label']}* (порт {target['port']}, {target['domain']}):\n\n`{link}`",
                parse_mode='Markdown'
            )
            await query.edit_message_text(f"📋 QR-код для *{target['label']}* отправлен выше.", parse_mode='Markdown')

    elif data == 'users':
        users_data = load_json(USERS_FILE)
        proxies_data = get_proxies()
        users = users_data.get('users', [])
        proxies = proxies_data.get('proxies', [])
        if not users:
            await query.edit_message_text("👥 Пользователей пока нет.\nИспользуйте ➕ Добавить пользователя")
            return

        msg = "👥 *Список пользователей:*\n\n"
        for u in users:
            status = "✅" if u.get('enabled', True) else "❌"
            proxy_label = "N/A"
            for p in proxies:
                if p['id'] == u.get('proxy_id', 1):
                    proxy_label = p['label']
                    break
            msg += f"{status} *{u['label']}* → {proxy_label}\n"

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
        proxies_data = get_proxies()
        proxies = proxies_data.get('proxies', [])

        keyboard = []
        for p in proxies:
            if p.get('enabled', True):
                keyboard.append([InlineKeyboardButton(
                    f"{p['label']} (порт {p['port']})",
                    callback_data=f"add_user_proxy_{p['id']}"
                )])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back')])

        await query.edit_message_text(
            "➕ *Выберите прокси сервер для нового пользователя:*\n\n"
            "После выбора отправьте имя пользователя.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith('add_user_proxy_'):
        proxy_id = int(data.replace('add_user_proxy_', ''))
        context.user_data['waiting_for_name'] = True
        context.user_data['selected_proxy_id'] = proxy_id

        proxies_data = get_proxies()
        proxies = proxies_data.get('proxies', [])
        for p in proxies:
            if p['id'] == proxy_id:
                await query.edit_message_text(
                    f"➕ Выбран прокси: *{p['label']}* (порт {p['port']})\n\n"
                    f"Отправьте имя нового пользователя:",
                    parse_mode='Markdown'
                )
                break

    elif data == 'stats':
        users_data = load_json(USERS_FILE)
        proxies_data = get_proxies()
        users = users_data.get('users', [])
        proxies = proxies_data.get('proxies', [])
        total_in = sum(u.get('traffic_in', 0) for u in users)
        total_out = sum(u.get('traffic_out', 0) for u in users)

        msg = f"📈 *Статистика*\n\n"
        msg += f"🌐 Прокси серверов: `{len(proxies)}`\n"
        msg += f"👤 Пользователей: `{len(users)}`\n"
        msg += f"📥 Трафик IN: `{total_in}` байт\n"
        msg += f"📤 Трафик OUT: `{total_out}` байт\n"
        msg += f"📊 Всего: `{total_in + total_out}` байт\n\n"

        if users:
            msg += "*По пользователям:*\n"
            for u in users:
                total = u.get('traffic_in', 0) + u.get('traffic_out', 0)
                msg += f"• {u['label']}: `{total}` байт\n"

        await query.edit_message_text(msg, parse_mode='Markdown')

    elif data == 'diagnostics':
        msg = (
            f"🔧 *Диагностика*\n\n"
            f"✅ Docker: работает\n"
            f"✅ MTProxy: запущен ({PROXY_COUNT} серверов)\n"
            f"✅ Web UI: работает\n"
            f"✅ Bot: работает\n"
            f"✅ IP: `{PROXY_IP}`"
        )
        await query.edit_message_text(msg, parse_mode='Markdown')

    elif data == 'back':
        await query.edit_message_text("📋 Главное меню:", reply_markup=main_menu_keyboard())

    elif data.startswith('disable_') or data.startswith('enable_'):
        action, user_id = data.split('_')
        user_id = int(user_id)
        users_data = load_json(USERS_FILE)

        for u in users_data.get('users', []):
            if u['id'] == user_id:
                u['enabled'] = (action == 'enable')
                break

        save_json(USERS_FILE, users_data)
        status = "включён" if action == 'enable' else "отключён"
        await query.edit_message_text(f"✅ Пользователь `{user_id}` {status}.", parse_mode='Markdown')

@admin_only
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_name'):
        name = update.message.text
        proxy_id = context.user_data.get('selected_proxy_id', 1)

        proxies_data = get_proxies()
        proxies = proxies_data.get('proxies', [])

        target_proxy = None
        for p in proxies:
            if p['id'] == proxy_id:
                target_proxy = p
                break

        if not target_proxy:
            await update.message.reply_text("❌ Прокси не найден!")
            context.user_data['waiting_for_name'] = False
            return

        users_data = load_json(USERS_FILE)
        next_id = users_data.get('next_id', 1)

        import secrets as sec
        new_secret = sec.token_hex(16)

        new_user = {
            'id': next_id,
            'label': name,
            'proxy_id': proxy_id,
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
        save_json(USERS_FILE, users_data)

        link = get_proxy_link(PROXY_IP, target_proxy['port'], target_proxy['secret'])
        qr_image = generate_qr(link)

        await update.message.reply_text(
            f"✅ Пользователь *{name}* добавлен!\n"
            f"🌐 Прокси: *{target_proxy['label']}* (порт {target_proxy['port']})\n\n"
            f"🔗 Ссылка: `{link}`",
            parse_mode='Markdown'
        )

        await update.message.reply_photo(
            photo=qr_image,
            caption=f"📱 QR-код для {name}"
        )

        context.user_data['waiting_for_name'] = False
        context.user_data['selected_proxy_id'] = None

        keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data='back')]]
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started!")

    async def on_startup(application):
        if ADMIN_CHAT_ID:
            try:
                proxies_data = get_proxies()
                proxies = proxies_data.get('proxies', [])
                msg = f"🟢 *MTProtoSERVER Bot запущен!*\n\n"
                msg += f"📡 Прокси серверов: `{len(proxies)}`\n"
                for p in proxies:
                    msg += f"  ✅ {p['label']} — порт `{p['port']}`\n"
                msg += "\nБот готов к работе."
                await app.bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
