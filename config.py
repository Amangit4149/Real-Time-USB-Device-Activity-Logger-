import json
import os

APP_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'app_config.json')
WHITELIST_PATH = os.path.join(os.path.dirname(__file__), 'whitelist.json')

DEFAULT_APP_CONFIG = {
    'alert_on_unknown_device': True,
    'whitelist_enabled': True,
    'capture_screenshots_on_unauthorized_insert': True,
    'screenshot_dir': os.path.join(os.path.dirname(__file__), 'screenshots'),
    'admin_mode_enabled': False,
    'email_alerts': {
        'enabled': False,
        'smtp_host': 'smtp.example.com',
        'smtp_port': 587,
        'use_tls': True,
        'username': '',
        'password': '',
        'sender': 'usb-logger@example.com',
        'recipients': []
    },
    'whitelisted_devices': [
        # Accept either serial numbers or VID:PID identifiers
        '0781:5567',
        '1234:ABCD'
    ]
}


def ensure_config_files():
    """Create config files with defaults if they do not exist."""
    try:
        if not os.path.exists(APP_CONFIG_PATH):
            with open(APP_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_APP_CONFIG, f, indent=2)

        if not os.path.exists(WHITELIST_PATH):
            whitelist_data = {
                'whitelisted_devices': DEFAULT_APP_CONFIG['whitelisted_devices']
            }
            with open(WHITELIST_PATH, 'w', encoding='utf-8') as f:
                json.dump(whitelist_data, f, indent=2)
    except Exception:
        pass


def load_app_config():
    """Load the application configuration from disk."""
    ensure_config_files()
    try:
        with open(APP_CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else DEFAULT_APP_CONFIG.copy()
    except Exception:
        return DEFAULT_APP_CONFIG.copy()


def save_app_config(data):
    """Save the application configuration back to disk."""
    try:
        with open(APP_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            return True
    except Exception:
        return False


def load_whitelist():
    """Load the whitelist entries from disk."""
    ensure_config_files()
    try:
        with open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                if data.get('whitelist_enabled', True) is False:
                    return []

                if 'whitelisted_devices' in data:
                    items = data.get('whitelisted_devices', [])
                elif 'whitelist' in data:
                    # Support legacy whitelist format where each entry is a dict
                    items = []
                    for entry in data.get('whitelist', []):
                        if isinstance(entry, dict):
                            vid = entry.get('vendor_id', '').strip().upper()
                            pid = entry.get('product_id', '').strip().upper()
                            if vid and pid:
                                items.append(f"{vid}:{pid}")
                        elif isinstance(entry, str):
                            items.append(entry)
                else:
                    items = []
            else:
                items = []
            return [str(x).strip().upper() for x in items if x]
    except Exception:
        return [str(x).strip().upper() for x in DEFAULT_APP_CONFIG['whitelisted_devices']]


def is_whitelist_enabled():
    """Return whether whitelist enforcement is enabled."""
    config = load_app_config()
    enabled = config.get('whitelist_enabled', True)
    if not enabled:
        return False

    try:
        with open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get('whitelist_enabled', True)
    except Exception:
        pass
    return True


def is_device_whitelisted(device_info):
    """Determine whether a USB device is authorized based on whitelist rules."""
    if not is_whitelist_enabled():
        return True

    whitelist = load_whitelist()
    if not whitelist:
        return False

    serial = (device_info.get('serial') or '').strip().upper()
    vid = (device_info.get('vid') or '').strip().upper()
    pid = (device_info.get('pid') or '').strip().upper()
    vidpid = f"{vid}:{pid}" if vid and pid else ''
    name = (device_info.get('name') or '').strip().upper()

    for entry in whitelist:
        entry = entry.strip().upper()
        if not entry:
            continue
        if entry == serial or entry == vidpid or entry in name:
            return True
    return False


def get_app_config():
    """Return the current application config."""
    return load_app_config()


def update_email_alert_settings(settings):
    """Update email alert settings and persist them to the app config."""
    config_data = load_app_config()
    email_alerts = config_data.get('email_alerts', DEFAULT_APP_CONFIG['email_alerts']).copy()
    email_alerts.update(settings or {})
    # Ensure recipients is always a list
    if 'recipients' in email_alerts and email_alerts['recipients'] is None:
        email_alerts['recipients'] = []
    config_data['email_alerts'] = email_alerts
    save_app_config(config_data)
    return email_alerts


def get_email_config():
    """Return the email alert settings."""
    config = load_app_config()
    email_alerts = config.get('email_alerts', {}).copy()
    merged = DEFAULT_APP_CONFIG['email_alerts'].copy()
    merged.update(email_alerts)
    return merged
