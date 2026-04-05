# MTProtoSERVER — Панель управления MTProto прокси

<div align="center">

![Версия](https://img.shields.io/badge/версия-2.0.0-brightgreen)
![Лицензия](https://img.shields.io/badge/лицензия-MIT-blue)
![Docker](https://img.shields.io/badge/docker-✅-blue)
![FakeTLS](https://img.shields.io/badge/FakeTLS-✅-orange)
![Мульти-ноды](https://img.shields.io/badge/мульти--ноды-✅-purple)
![2FA](https://img.shields.io/badge/2FA-TOTP-red)

**Полноценная платформа для управления MTProto прокси с обходом блокировок, мульти-нодами, мониторингом и управлением клиентами**

[🇷🇺 Русский](#-описание) • [🇬🇧 English](#-english)

</div>

---

<a id="-описание"></a>
## 📖 Описание

**MTProtoSERVER** — это полноценная платформа для развёртывания и управления MTProto прокси серверами с обходом блокировок. Работает на базе **mtg v2** — самого современного движка MTProto.

### Ключевые возможности:

- 🛡️ **FakeTLS маскировка** — трафик неотличим от обычного HTTPS
- 🇷🇺 **Работает в РФ** — обход DPI и блокировок
- 🖥️ **Мульти-ноды** — управление прокси на нескольких серверах
- 👥 **Управление клиентами** — отдельные ссылки с лимитами и автостопом
- 📊 **Мониторинг в реальном времени** — трафик, подключения, графики 24ч
- 🌐 **Web UI** — полная панель управления
- 🤖 **Telegram бот** — управление из мессенджера
- 🔒 **2FA (TOTP)** — Google Authenticator, Aegis, Authy
- 🧦 **SOCKS5 прокси** — универсальный прокси (Dante)
- 🌐 **HTTP/HTTPS прокси** — прокси для браузеров (Squid)
- 💰 **Ad-Tag** — монетизация через Telegram
- 💾 **Бэкап/Восстановление** — из Web UI
- 🌍 **GeoIP** — блокировка стран
- 🚀 **Speedtest** — тест скорости из панели
- 🔔 **Webhook** — уведомления в Discord/Slack
- 🌐 **i18n** — русский и английский
- 🖼️ **Свой логотип** — загрузка из панели

---

## ⭐ Возможности

### 🖥️ Управление нодами
| Функция | Описание |
|---------|----------|
| **Добавление/редактирование/удаление** | Управление несколькими прокси серверами |
| **SSH-подключение** | По паролю или приватному ключу |
| **Флаги стран** | Визуальная навигация по нодам |
| **Проверка связи** | Ping и проверка статуса прямо из UI |
| **Синхронизация** | Получение данных клиентов с удалённых нод |

### 👥 Управление клиентами
| Функция | Описание |
|---------|----------|
| **Автоназначение порта и секрета** | При создании клиента всё генерируется автоматически |
| **Запуск / остановка** | Управление отдельными клиентами |
| **QR-коды и ссылки** | Быстрое подключение через Telegram |
| **Синхронизация с нодой** | Подтягивание существующих клиентов с удалённого сервера |
| **Массовый просмотр** | Все клиенты со всех нод в одной таблице |
| **Ротация секрета** | Генерация нового ключа, старые ссылки перестают работать |
| **Сброс трафика** | Обнуление счётчиков вручную |

### 📊 Мониторинг в реальном времени
| Функция | Описание |
|---------|----------|
| **Трафик rx/tx** | За текущий период и за всё время |
| **Уникальные IP** | Количество активных подключений |
| **График 24ч (sparkline)** | Мини-график подключений прямо в таблице |
| **Онлайн-статус из кэша** | Ответ < 5 мс без задержки |
| **Ресурсы сервера** | CPU, RAM, диск |

### 🎯 Лимиты и автоматизация
| Функция | Описание |
|---------|----------|
| **Лимит трафика (ГБ)** | Автостоп при превышении |
| **Лимит устройств** | Автостоп при достижении лимита уникальных IP |
| **Срок действия** | Автостоп по истечении даты |
| **Автосброс трафика** | По расписанию: каждый день / месяц / год |

### 🔒 Безопасность
| Функция | Описание |
|---------|----------|
| **Токен-авторизация** | Защита панели и API |
| **TOTP 2FA** | Google Authenticator, Aegis, Authy |
| **IP Blacklist/Whitelist** | Постраничный контроль доступа |
| **Управление файрволом** | Открытие/закрытие портов из UI |
| **Rate limiting** | Настраиваемое ограничение запросов |

### 🌐 Интерфейс
| Функция | Описание |
|---------|----------|
| **Тёмная и светлая тема** | Переключение с сохранением |
| **Два языка** | Русский и английский |
| **Свой логотип** | Загрузка в сайдбар из настроек |
| **Адаптивный дизайн** | Работает на мобильных устройствах |

### 🧦 SOCKS5 прокси (Dante)
| Функция | Описание |
|---------|----------|
| **Универсальный прокси** | Работает с любым приложением: браузер, Telegram, curl |
| **Мульти-юзеры** | Несколько пользователей с разными логинами/паролями |
| **Аутентификация** | Логин/пароль для каждого пользователя |
| **Любые приложения** | Браузер, Telegram, системный прокси, скрипты |

### 🌐 HTTP/HTTPS прокси (Squid)
| Функция | Описание |
|---------|----------|
| **Самый популярный HTTP прокси** | Squid — стандарт индустрии |
| **Кэширование** | Ускорение загрузки за счёт кэша |
| **Basic auth** | Аутентификация по логину/паролю |
| **HTTPS поддержка** | Проксирование HTTPS трафика |

### 💰 Монетизация и уведомления
| Функция | Описание |
|---------|----------|
| **Ad-Tag** | Встроенная реклама от Telegram (@MTProxyBot) |
| **Управление из Web UI** | Установка и смена Ad-Tag из панели |
| **Webhook уведомления** | Алерты в Discord, Slack, любой webhook URL |
| **Тест webhook** | Проверка работоспособности из Web UI |

### 🛠️ Диагностика и обслуживание
| Функция | Описание |
|---------|----------|
| **Speedtest** | Тест скорости (download/upload/ping) из Web UI |
| **Health Check** | Полная проверка системы одной кнопкой |
| **Бэкап/Восстановление** | Создание и восстановление из Web UI |
| **Логи** | Просмотр логов контейнеров в реальном времени |
| **QR-коды** | Генерация QR для ссылок прокси |
| **Экспорт конфигов** | Скачивание всех настроек в ZIP |

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│              Панель управления (Web UI)                       │
│  FastAPI + Jinja2 + Chart.js                                  │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐           │
│  │Дашборд  │ │ Клиенты  │ │  Ноды  │ │ Настройки│           │
│  └─────────┘ └──────────┘ └────────┘ └──────────┘           │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │ Нода 1  │       │ Нода 2  │       │ Нода N  │
   │(Локальная)      │Удалённая│       │Удалённая│
   │         │       │         │       │         │
   │ ┌─────┐ │       │ ┌─────┐ │       │ ┌─────┐ │
   │ │MTG  │ │       │ │MTG  │ │       │ │MTG  │ │
   │ │Proxy│ │       │ │Proxy│ │       │ │Proxy│ │
   │ └─────┘ │       │ └─────┘ │       │ └─────┘ │
   │ ┌─────┐ │       │ ┌─────┐ │       │ ┌─────┐ │
   │ │Agent│ │◄──────│ │Agent│ │◄──────│ │Agent│ │
   │ │:9876│ │ HTTP  │ │:9876│ │ HTTP  │ │:9876│ │
   │ └─────┘ │       │ └─────┘ │       │ └─────┘ │
   └─────────┘       └─────────┘       └─────────┘
```

### Компоненты

| Компонент | Описание |
|-----------|----------|
| **Web UI** | Панель на FastAPI с Jinja2 шаблонами |
| **MTG Proxy** | nineseconds/mtg:2 — движок MTProto с FakeTLS |
| **MTG Agent** | HTTP-агент на каждой ноде для мониторинга |
| **Telegram Bot** | python-telegram-bot для удалённого управления |
| **SOCKS5** | Dante — универсальный SOCKS5 прокси |
| **HTTP Proxy** | Squid — HTTP/HTTPS прокси с кэшированием |

---

## 🚀 Быстрая установка

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/install.sh)"
```

> ⚠️ **Требования:** Linux (Ubuntu/Debian/CentOS), root доступ, открытый порт 443

---

## 📖 Пошаговая установка

### 1. Подготовка сервера

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Запуск установщика

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/install.sh)"
```

Установщик проведёт через все шаги:

1. **Проверка системы** — определение ОС, установка зависимостей
2. **Установка Docker** — автоматически, если не установлен
3. **MTProto прокси** — сколько создать (1-10), порты, домены маскировки
4. **Telegram бот** — опционально, автоопределение Chat ID админа
5. **SOCKS5 прокси** — опционально, с аутентификацией
6. **HTTP/HTTPS прокси** — опционально, Squid с авторизацией
7. **Ad-Tag** — опционально, монетизация
8. **GeoIP блокировка** — опционально, коды стран
9. **Webhook уведомления** — опционально, Discord/Slack
10. **Запуск** — запуск всех контейнеров

### 3. Доступ к Web UI

После установки откройте: `http://ВАШ_IP:8080`

### 4. Установка MTG Agent на удалённые ноды

На каждом удалённом сервере:

```bash
curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/agent/install.sh | bash -s -- --port 9876 --token ВАШ_СЕКРЕТНЫЙ_ТОКЕН
```

Затем добавьте ноду в Web UI → Ноды.

---

## 🤖 MTG Agent

MTG Agent — лёгкий HTTP-сервис на FastAPI, устанавливаемый на каждую прокси-ноду. Предоставляет:

- **Данные клиентов в реальном времени** — трафик, уникальные IP, статус
- **История подключений за 24ч** — для sparkline графиков
- **Управление жизненным циклом** — создание, запуск, остановка, перезапуск, удаление
- **Мониторинг системы** — CPU, RAM, диск
- **Кэширование** — ответы <5ms из кэша (обновление каждые 30с)

### API Агента

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/health` | GET | Проверка работоспособности |
| `/clients` | GET | Список всех MTG клиентов со статистикой |
| `/clients/{label}/history` | GET | История подключений за 24ч |
| `/clients/{label}/start` | POST | Запустить клиента |
| `/clients/{label}/stop` | POST | Остановить клиента |
| `/clients/{label}/restart` | POST | Перезапустить клиента |
| `/clients/create` | POST | Создать нового MTG клиента |
| `/clients/{label}` | DELETE | Удалить клиента |
| `/system` | GET | Ресурсы системы |

Все эндпоинты требуют заголовок `x-token`.

---

## 🎛️ Web UI

### Страницы

| Страница | Описание |
|----------|----------|
| **Дашборд** | Обзор, Docker контейнеры, ресурсы, быстрые действия |
| **Клиенты** | Добавление/управление клиентами с лимитами, QR-коды, sparkline |
| **Ноды** | Добавление/управление нодами, ping, синхронизация, установка агента |
| **Статистика** | Графики трафика, детали клиентов, ресурсы сервера |
| **SOCKS5** | Информация о SOCKS5 прокси и управление пользователями |
| **HTTP/HTTPS** | Информация о HTTP прокси и инструкции |
| **Логи** | Просмотр логов контейнеров в реальном времени |
| **Бэкап** | Создание, восстановление, удаление бэкапов |
| **Безопасность** | IP blacklist/whitelist, файрвол, rate limiting, экспорт |
| **Настройки** | Токен, 2FA, логотип, Ad-Tag, ротация домена, webhook, speedtest |

---

## 🤖 Telegram Bot

Команды доступны через inline меню:

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню с inline кнопками |
| 📊 Статус | Информация о прокси |
| 🌐 Прокси | Список всех прокси серверов |
| 👥 Пользователи | Список и управление |
| ➕ Добавить | Создание нового пользователя |
| 📈 Статистика | Общая статистика трафика |
| 🔧 Диагностика | Проверка состояния системы |

---

## 📡 API Reference

### Аутентификация

```bash
curl -H "x-token: ВАШ_ТОКЕН" http://ВАШ_IP:8080/api/status
```

### Ключевые эндпоинты

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/api/status` | GET | Статус системы |
| `/api/clients/add` | POST | Добавить клиента |
| `/api/clients/{id}/toggle` | POST | Вкл/выкл клиента |
| `/api/clients/{id}/delete` | POST | Удалить клиента |
| `/api/clients/{id}/rotate` | POST | Ротация секрета |
| `/api/clients/{id}/reset-traffic` | POST | Сброс трафика |
| `/api/nodes/add` | POST | Добавить ноду |
| `/api/nodes/{id}/ping` | POST | Пинг ноды |
| `/api/nodes/{id}/sync` | POST | Синхронизация клиентов |
| `/api/system/backup` | POST | Создать бэкап |
| `/api/system/restore` | POST | Восстановить из бэкапа |
| `/api/system/health` | GET | Проверка здоровья |
| `/api/system/speedtest` | GET | Тест скорости |
| `/api/qr?text=...` | GET | Генерация QR-кода |
| `/api/metrics` | GET | Prometheus метрики |

---

## 🛡️ Безопасность

### Рекомендации

1. **Включите 2FA** — Настройки → Двухфакторная аутентификация
2. **Смените токен** — Настройки → Аутентификация
3. **Используйте сложные токены агента** — Разный токен на каждую ноду
4. **Откройте только нужные порты** — 443 для прокси, 8080 для Web UI
5. **Включите GeoIP блокировку** — Блокируйте нежелательные страны
6. **Регулярные бэкапы** — Используйте страницу Бэкап

### Файрвол (UFW)

```bash
sudo ufw allow 443/tcp    # MTProto прокси
sudo ufw allow 8080/tcp   # Web UI (ограничьте по IP)
sudo ufw allow 1080/tcp   # SOCKS5 (если включён)
sudo ufw allow 3128/tcp   # HTTP прокси (если включён)
sudo ufw enable
```

---

## 🔧 Устранение проблем

### Прокси не подключается

1. Проверьте контейнеры: `docker compose ps`
2. Проверьте порт 443: `ss -tlnp | grep 443`
3. Проверьте файрвол: `sudo ufw status`
4. Проверьте логи: `docker compose logs mtproto-proxy`

### Web UI не открывается

1. Проверьте контейнер: `docker compose ps mtproto-webui`
2. Проверьте порт: `ss -tlnp | grep 8080`
3. Откройте порт: `sudo ufw allow 8080/tcp`

### Агент не отвечает

1. Проверьте агент: `curl http://IP_НОДЫ:9876/health`
2. Проверьте токен: Убедитесь что токен совпадает в панели и агенте
3. Перезапустите: `cd /opt/mtg-agent && docker compose restart`

### Health Check

```bash
curl http://ВАШ_IP:8080/api/system/health
```

---

## ❓ FAQ

### Q: Сколько клиентов можно создать?
A: Ограничено ресурсами сервера. На минимальном VPS (1 ядро, 512MB RAM) — до 100 клиентов.

### Q: Как добавить клиента?
A: Web UI → Клиенты → форма добавления, или через API `/api/clients/add`.

### Q: Как добавить удалённую ноду?
A: Установите агент на удалённый сервер, затем добавьте в Web UI → Ноды.

### Q: Как сменить домен маскировки?
A: Настройки → Ротация домена, или `bash /opt/mtprotoserver/scripts/rotate-domain.sh`.

### Q: Как обновить?
A: `cd /opt/mtprotoserver && docker compose pull && docker compose up -d`

### Q: Это легально?
A: MTProto — официальный протокол прокси от Telegram. Использование прокси для доступа к легальным ресурсам не запрещено.

---

## 🗑️ Удаление

```bash
curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/uninstall.sh | sudo bash -s -- -y
```

Или вручную:
```bash
cd /opt/mtprotoserver
docker compose down
cd ..
sudo rm -rf /opt/mtprotoserver
```

---

## 📁 Структура проекта

```
MTProtoSERVER/
├── install.sh                    # Главный установщик (интерактивный)
├── uninstall.sh                  # Скрипт удаления
├── README.md                     # Документация (RU/EN)
├── .gitignore
│
├── agent/                        # MTG Agent для удалённых нод
│   ├── Dockerfile
│   ├── agent.py                  # FastAPI агент для мониторинга
│   ├── requirements.txt
│   └── install.sh                # Установщик агента в один клик
│
├── webui/                        # Web Панель управления
│   ├── Dockerfile
│   ├── app.py                    # FastAPI приложение
│   ├── requirements.txt
│   ├── templates/                # Jinja2 HTML шаблоны
│   │   ├── base.html             # Базовый layout с сайдбаром
│   │   ├── dashboard.html        # Главный дашборд
│   │   ├── clients.html          # Управление клиентами
│   │   ├── nodes.html            # Управление нодами
│   │   ├── stats.html            # Статистика и графики
│   │   ├── settings.html         # Настройки и 2FA
│   │   ├── security.html         # Безопасность и файрвол
│   │   ├── logs.html             # Логи контейнеров
│   │   ├── backup.html           # Бэкап и восстановление
│   │   ├── socks5.html           # Управление SOCKS5
│   │   └── http_proxy.html       # Информация о HTTP прокси
│   └── static/
│       ├── css/style.css         # Стили (тёмная/светлая тема)
│       └── js/app.js             # JavaScript (i18n, тема)
│
├── bot/                          # Telegram Бот
│   ├── Dockerfile
│   ├── bot.py                    # Telegram бот
│   └── requirements.txt
│
├── scripts/                      # Вспомогательные скрипты
│   ├── auto-heal.sh              # Автоперезапуск при падении
│   ├── auto-update.sh            # Автообновление образов
│   ├── backup.sh                 # Бэкап конфигов
│   ├── monitor.sh                # Мониторинг доступности
│   ├── rotate-domain.sh          # Ротация домена
│   ├── health-check.sh           # Диагностика системы
│   ├── speedtest.sh              # Тест скорости
│   ├── add-proxy.sh              # Добавить прокси интерактивно
│   └── remove-proxy.sh           # Удалить прокси по метке
│
└── config/                       # Конфигурационные файлы
    ├── domains.txt               # Список доменов FakeTLS
    └── geoblock.txt              # GeoIP блок-лист
```

---

## 📄 Лицензия

MIT License — свободное использование с указанием авторства.

---

<div align="center">

**MTProtoSERVER v2.0.0** | 2026

Сделано с ❤️ для свободного доступа к Telegram

</div>

---

<a id="-english"></a>
<br>

# 🇬🇧 English Version

## 📖 Overview

**MTProtoSERVER** is a complete platform for deploying and managing MTProto proxy servers with bypass capabilities for Russia and other restricted regions. Built on **mtg v2** — the most modern MTProto engine.

### Key Features:

- 🛡️ **FakeTLS cloaking** — traffic indistinguishable from regular HTTPS
- 🇷🇺 **Works in Russia** — bypasses DPI and blocking
- 🖥️ **Multi-node** — manage proxy servers across multiple machines
- 👥 **Client management** — per-client links with limits and auto-stop
- 📊 **Real-time monitoring** — traffic, connections, 24h sparkline charts
- 🌐 **Web UI** — full management dashboard
- 🤖 **Telegram bot** — manage from messenger
- 🔒 **2FA (TOTP)** — Google Authenticator, Aegis, Authy
- 🧦 **SOCKS5** — universal proxy (Dante)
- 🌐 **HTTP/HTTPS** — proxy for browsers (Squid)
- 💰 **Ad-Tag** — monetization via Telegram
- 💾 **Backup/Restore** — from Web UI
- 🌍 **GeoIP** — country blocking
- 🚀 **Speedtest** — from Web UI
- 🔔 **Webhooks** — Discord, Slack notifications
- 🌐 **i18n** — Russian & English
- 🖼️ **Custom logo** — upload your own

---

## ⭐ Features

### 🖥️ Node Management
| Feature | Description |
|---------|-------------|
| **Add/Edit/Delete nodes** | Manage multiple proxy servers |
| **SSH connection** | By password or private key |
| **Country flags** | Visual navigation |
| **Ping & status check** | Test connectivity from UI |
| **Agent sync** | Sync clients from remote nodes |

### 👥 Client Management
| Feature | Description |
|---------|-------------|
| **Auto port & secret** | Automatically assigned on creation |
| **Start/Stop** | Individual client control |
| **QR codes & links** | Quick connection via Telegram |
| **Sync from nodes** | Pull existing clients from remote nodes |
| **Mass view** | See all clients across all nodes |
| **Secret rotation** | Generate new secret, old links die |
| **Traffic reset** | Manual reset per client |

### 📊 Real-time Monitoring
| Feature | Description |
|---------|-------------|
| **RX/TX traffic** | Current period and lifetime |
| **Unique IPs** | Active connections count |
| **24h sparkline** | Connection chart in table |
| **Online cache** | <5ms response from cache |
| **Server resources** | CPU, RAM, Disk usage |

### 🎯 Limits & Automation
| Feature | Description |
|---------|-------------|
| **Traffic limit (GB)** | Auto-stop when exceeded |
| **Device limit** | Auto-stop on unique IP threshold |
| **Expiry date** | Auto-stop after date |
| **Auto-reset traffic** | Daily / Monthly / Yearly schedule |

### 🔒 Security
| Feature | Description |
|---------|-------------|
| **Token auth** | API and UI authentication |
| **TOTP 2FA** | Google Authenticator, Aegis, Authy |
| **IP Blacklist/Whitelist** | Per-IP access control |
| **Firewall management** | Open/close ports from UI |
| **Rate limiting** | Configurable request limits |

### 🌐 Interface
| Feature | Description |
|---------|-------------|
| **Dark/Light theme** | Toggle with persistence |
| **RU/EN languages** | Two languages with toggle |
| **Custom logo** | Upload your own logo |
| **Responsive design** | Works on mobile devices |

### 🧦 SOCKS5 Proxy (Dante)
| Feature | Description |
|---------|-------------|
| **Universal proxy** | Works with any app: browser, Telegram, curl |
| **Multi-user** | Multiple users with different credentials |
| **Authentication** | Login/password per user |
| **Any application** | Browser, Telegram, system proxy, scripts |

### 🌐 HTTP/HTTPS Proxy (Squid)
| Feature | Description |
|---------|-------------|
| **Most popular HTTP proxy** | Squid — industry standard |
| **Caching** | Speed up via cache |
| **Basic auth** | Username/password authentication |
| **HTTPS support** | HTTPS traffic proxying |

### 💰 Monetization & Notifications
| Feature | Description |
|---------|-------------|
| **Ad-Tag** | Built-in Telegram ads (@MTProxyBot) |
| **Web UI management** | Set/change Ad-Tag from panel |
| **Webhook alerts** | Discord, Slack, any webhook URL |
| **Webhook test** | Verify from Web UI |

### 🛠️ Diagnostics & Maintenance
| Feature | Description |
|---------|-------------|
| **Speedtest** | Download/upload/ping from Web UI |
| **Health check** | Full system check with one click |
| **Backup/Restore** | Create and restore from Web UI |
| **Logs** | View container logs in real-time |
| **QR codes** | Generate QR for proxy links |
| **Config export** | Download all configs as ZIP |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Panel (Web UI)                     │
│  FastAPI + Jinja2 + Chart.js                                  │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐           │
│  │Dashboard│ │ Clients  │ │ Nodes  │ │ Settings │           │
│  └─────────┘ └──────────┘ └────────┘ └──────────┘           │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │ Node 1  │       │ Node 2  │       │ Node N  │
   │ (Local) │       │ Remote  │       │ Remote  │
   │         │       │         │       │         │
   │ ┌─────┐ │       │ ┌─────┐ │       │ ┌─────┐ │
   │ │MTG  │ │       │ │MTG  │ │       │ │MTG  │ │
   │ │Proxy│ │       │ │Proxy│ │       │ │Proxy│ │
   │ └─────┘ │       │ └─────┘ │       │ └─────┘ │
   │ ┌─────┐ │       │ ┌─────┐ │       │ ┌─────┐ │
   │ │Agent│ │◄──────│ │Agent│ │◄──────│ │Agent│ │
   │ │:9876│ │ HTTP  │ │:9876│ │ HTTP  │ │:9876│ │
   │ └─────┘ │       │ └─────┘ │       │ └─────┘ │
   └─────────┘       └─────────┘       └─────────┘
```

### Components

| Component | Description |
|-----------|-------------|
| **Web UI** | FastAPI dashboard with Jinja2 templates |
| **MTG Proxy** | nineseconds/mtg:2 — MTProto engine with FakeTLS |
| **MTG Agent** | FastAPI HTTP agent on each node for monitoring |
| **Telegram Bot** | python-telegram-bot for remote management |
| **SOCKS5** | Dante — universal SOCKS5 proxy |
| **HTTP Proxy** | Squid — HTTP/HTTPS proxy with caching |

---

## 🚀 Quick Install

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/install.sh)"
```

> ⚠️ **Requirements:** Linux (Ubuntu/Debian/CentOS), root access, open port 443

---

## 📖 Step-by-Step Install

### 1. Prepare Server

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Run Installer

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/install.sh)"
```

The installer will guide you through:

1. **System check** — OS detection, dependencies
2. **Docker install** — automatic if not present
3. **MTProto proxies** — how many, ports, domains (1-10 proxies)
4. **Telegram bot** — optional, auto-detects admin Chat ID
5. **SOCKS5 proxy** — optional, with auth
6. **HTTP/HTTPS proxy** — optional, Squid with auth
7. **Ad-Tag** — optional, monetization
8. **GeoIP blocking** — optional, country codes
9. **Webhook notifications** — optional, Discord/Slack
10. **Start** — launches everything

### 3. Access Web UI

After installation, open: `http://YOUR_IP:8080`

### 4. Install MTG Agent on Remote Nodes

On each remote server:

```bash
curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/agent/install.sh | bash -s -- --port 9876 --token YOUR_SECRET_TOKEN
```

Then add the node in Web UI → Nodes page.

---

## 🤖 MTG Agent

The MTG Agent is a lightweight FastAPI HTTP service installed on each proxy node. It provides:

- **Real-time client data** — traffic, unique IPs, status
- **24h connection history** — sparkline charts
- **Client lifecycle** — create, start, stop, restart, delete
- **System monitoring** — CPU, RAM, disk
- **Caching** — <5ms responses from 30s cache

### Agent API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/clients` | GET | List all MTG clients with stats |
| `/clients/{label}/history` | GET | 24h connection history |
| `/clients/{label}/start` | POST | Start a client |
| `/clients/{label}/stop` | POST | Stop a client |
| `/clients/{label}/restart` | POST | Restart a client |
| `/clients/create` | POST | Create new MTG client |
| `/clients/{label}` | DELETE | Delete a client |
| `/system` | GET | System resources |

All endpoints require `x-token` header.

---

## 🎛️ Web UI

### Pages

| Page | Description |
|------|-------------|
| **Dashboard** | Overview, Docker containers, resources, quick actions |
| **Clients** | Add/manage clients with limits, QR codes, sparklines |
| **Nodes** | Add/manage nodes, ping test, sync, agent install |
| **Statistics** | Traffic charts, client details, system resources |
| **SOCKS5** | SOCKS5 proxy info and user management |
| **HTTP/HTTPS** | HTTP proxy info and usage instructions |
| **Logs** | Container logs in real-time |
| **Backup** | Create, restore, delete backups |
| **Security** | IP blacklist/whitelist, firewall, rate limiting, export |
| **Settings** | Auth token, 2FA, logo, Ad-Tag, domain rotation, webhook, speedtest |

---

## 🤖 Telegram Bot

Commands available through inline menu:

| Command | Description |
|---------|-------------|
| `/start` | Main menu with inline buttons |
| 📊 Status | Proxy info and stats |
| 🌐 Proxies | List all proxy servers |
| 👥 Users | List and manage users |
| ➕ Add User | Create new user with proxy selection |
| 📈 Statistics | Overall traffic stats |
| 🔧 Diagnostics | System health check |

---

## 📡 API Reference

### Authentication

```bash
curl -H "x-token: YOUR_TOKEN" http://YOUR_IP:8080/api/status
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/clients/add` | POST | Add new client |
| `/api/clients/{id}/toggle` | POST | Enable/disable client |
| `/api/clients/{id}/delete` | POST | Delete client |
| `/api/clients/{id}/rotate` | POST | Rotate client secret |
| `/api/clients/{id}/reset-traffic` | POST | Reset traffic counters |
| `/api/nodes/add` | POST | Add new node |
| `/api/nodes/{id}/ping` | POST | Ping node |
| `/api/nodes/{id}/sync` | POST | Sync clients from node |
| `/api/system/backup` | POST | Create backup |
| `/api/system/restore` | POST | Restore from backup |
| `/api/system/health` | GET | Health check |
| `/api/system/speedtest` | GET | Speed test |
| `/api/qr?text=...` | GET | Generate QR code |
| `/api/metrics` | GET | Prometheus metrics |

---

## 🛡️ Security

### Recommendations

1. **Enable 2FA** — Settings → Two-Factor Authentication
2. **Change default token** — Settings → Authentication
3. **Use strong agent tokens** — Different token per node
4. **Open only required ports** — 443 for proxy, 8080 for Web UI
5. **Enable GeoIP blocking** — Block unwanted countries
6. **Regular backups** — Use the Backup page

### Firewall (UFW)

```bash
sudo ufw allow 443/tcp    # MTProto proxy
sudo ufw allow 8080/tcp   # Web UI (restrict by IP)
sudo ufw allow 1080/tcp   # SOCKS5 (if enabled)
sudo ufw allow 3128/tcp   # HTTP proxy (if enabled)
sudo ufw enable
```

---

## 🔧 Troubleshooting

### Proxy not connecting

1. Check containers: `docker compose ps`
2. Check port 443: `ss -tlnp | grep 443`
3. Check firewall: `sudo ufw status`
4. Check logs: `docker compose logs mtproto-proxy`

### Web UI not loading

1. Check container: `docker compose ps mtproto-webui`
2. Check port: `ss -tlnp | grep 8080`
3. Open port: `sudo ufw allow 8080/tcp`

### Agent not responding

1. Check agent: `curl http://NODE_IP:9876/health`
2. Check token: Ensure token matches in both panel and agent
3. Restart agent: `cd /opt/mtg-agent && docker compose restart`

### Health Check

```bash
curl http://YOUR_IP:8080/api/system/health
```

---

## ❓ FAQ

### Q: How many clients can I create?
A: Limited by server resources. On a minimal VPS (1 core, 512MB RAM) — up to 100 clients.

### Q: How do I add a client?
A: Web UI → Clients → Add Client form, or via API `/api/clients/add`.

### Q: How do I add a remote node?
A: Install the agent on the remote server, then add it in Web UI → Nodes.

### Q: How do I change the masking domain?
A: Settings → Domain Rotation, or run `bash /opt/mtprotoserver/scripts/rotate-domain.sh`.

### Q: How do I update?
A: `cd /opt/mtprotoserver && docker compose pull && docker compose up -d`

### Q: Is this legal?
A: MTProto is Telegram's official proxy protocol. Using proxies to access legal resources is not prohibited.

---

## 🗑️ Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/Therealwh/MTProtoSERVER/main/uninstall.sh | sudo bash -s -- -y
```

Or manually:
```bash
cd /opt/mtprotoserver
docker compose down
cd ..
sudo rm -rf /opt/mtprotoserver
```

---

## 📁 Project Structure

```
MTProtoSERVER/
├── install.sh                    # Main installer (interactive)
├── uninstall.sh                  # Uninstaller
├── README.md                     # Documentation (RU/EN)
├── .gitignore
│
├── agent/                        # MTG Agent for remote nodes
│   ├── Dockerfile
│   ├── agent.py                  # FastAPI agent for monitoring
│   ├── requirements.txt
│   └── install.sh                # One-click agent installer
│
├── webui/                        # Web Control Panel
│   ├── Dockerfile
│   ├── app.py                    # FastAPI application
│   ├── requirements.txt
│   ├── templates/                # Jinja2 HTML templates
│   │   ├── base.html             # Base layout with sidebar
│   │   ├── dashboard.html        # Main dashboard
│   │   ├── clients.html          # Client management
│   │   ├── nodes.html            # Node management
│   │   ├── stats.html            # Statistics & charts
│   │   ├── settings.html         # Settings & 2FA
│   │   ├── security.html         # Security & firewall
│   │   ├── logs.html             # Container logs
│   │   ├── backup.html           # Backup & restore
│   │   ├── socks5.html           # SOCKS5 management
│   │   └── http_proxy.html       # HTTP proxy info
│   └── static/
│       ├── css/style.css         # Styles (dark/light theme)
│       └── js/app.js             # JavaScript (i18n, theme)
│
├── bot/                          # Telegram Bot
│   ├── Dockerfile
│   ├── bot.py                    # Telegram bot
│   └── requirements.txt
│
├── scripts/                      # Helper scripts
│   ├── auto-heal.sh              # Auto-restart on failure
│   ├── auto-update.sh            # Auto-update images
│   ├── backup.sh                 # Config backup
│   ├── monitor.sh                # Availability monitoring
│   ├── rotate-domain.sh          # Domain rotation
│   ├── health-check.sh           # System diagnostics
│   ├── speedtest.sh              # Speed test
│   ├── add-proxy.sh              # Add proxy interactively
│   └── remove-proxy.sh           # Remove proxy by label
│
└── config/                       # Configuration files
    ├── domains.txt               # FakeTLS domain list
    └── geoblock.txt              # GeoIP blocklist
```

---

## 📄 License

MIT License — free to use with attribution.

---

<div align="center">

**MTProtoSERVER v2.0.0** | 2026

Made with ❤️ for free access to Telegram

</div>
