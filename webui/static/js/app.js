const I18N = {
    ru: { dashboard: 'Дашборд', clients: 'Клиенты', nodes: 'Ноды', stats: 'Статистика', settings: 'Настройки', security: 'Безопасность', logs: 'Логи', backup: 'Бэкап' },
    en: { dashboard: 'Dashboard', clients: 'Clients', nodes: 'Nodes', stats: 'Statistics', settings: 'Settings', security: 'Security', logs: 'Logs', backup: 'Backup' }
};

function showToast(msg) {
    const t = document.createElement('div');
    t.className = 'toast'; t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 3000);
}

function toggleTheme() {
    const html = document.documentElement;
    const next = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}

function toggleLang() {
    const current = localStorage.getItem('lang') || 'ru';
    const next = current === 'ru' ? 'en' : 'ru';
    localStorage.setItem('lang', next);
    document.getElementById('current-lang').textContent = next.toUpperCase();
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (I18N[next] && I18N[next][key]) el.textContent = I18N[next][key];
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const theme = localStorage.getItem('theme');
    if (theme) document.documentElement.setAttribute('data-theme', theme);
    const lang = localStorage.getItem('lang') || 'ru';
    const el = document.getElementById('current-lang');
    if (el) el.textContent = lang.toUpperCase();
    document.querySelectorAll('[data-i18n]').forEach(e => {
        const key = e.getAttribute('data-i18n');
        if (I18N[lang] && I18N[lang][key]) e.textContent = I18N[lang][key];
    });
});
