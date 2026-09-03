import os
import json
import signal
import logging

# Use separate, standard directories for config and data.
# These are intended to be mounted as separate volumes in Docker.
CONFIG_DIR = os.environ.get('CONFIG_DIR', '/config')
WEBDAV_DIR = os.environ.get('WEBDAV_DIR', '/webdav')

CONFIG_FILE = os.path.join(CONFIG_DIR, 'settings.json')
DATABASE_PATH = os.path.join(CONFIG_DIR, 'app.db')
GUNICORN_PID_FILE = "/tmp/gunicorn.pid"

# Define default configuration and environment variable mappings
DEFAULT_CONFIG = {
    # Library provider selection: 'calibre' (default) or 'talebook'
    'LIBRARY_PROVIDER': {'env': 'LIBRARY_PROVIDER', 'default': 'calibre'},

    # Global Calibre related settings
    'CALIBRE_URL': {'env': 'CALIBRE_URL', 'default': 'http://localhost:8081'},
    'CALIBRE_USERNAME': {'env': 'CALIBRE_USERNAME', 'default': ''},
    'CALIBRE_PASSWORD': {'env': 'CALIBRE_PASSWORD', 'default': ''},
    'CALIBRE_DEFAULT_LIBRARY_ID': {'env': 'CALIBRE_DEFAULT_LIBRARY_ID', 'default': 'Calibre_Library'},
    'CALIBRE_ADD_DUPLICATES': {'env': 'CALIBRE_ADD_DUPLICATES', 'default': False},

    # Talebook connection settings (used when LIBRARY_PROVIDER=talebook)
    'TALEBOOK_URL': {'env': 'TALEBOOK_URL', 'default': ''},
    'TALEBOOK_USERNAME': {'env': 'TALEBOOK_USERNAME', 'default': ''},
    'TALEBOOK_PASSWORD': {'env': 'TALEBOOK_PASSWORD', 'default': ''},
    'TALEBOOK_TIMEOUT': {'env': 'TALEBOOK_TIMEOUT', 'default': 15},
    'TALEBOOK_VERIFY_SSL': {'env': 'TALEBOOK_VERIFY_SSL', 'default': True},
    
    # Global application security settings
    'SECRET_KEY': {'env': 'SECRET_KEY', 'default': ''}, # Will be generated on first load
    'LOGIN_MAX_ATTEMPTS': {'env': 'LOGIN_MAX_ATTEMPTS', 'default': 5},
    'SESSION_LIFETIME_DAYS': {'env': 'SESSION_LIFETIME_DAYS', 'default': 7},
    'ENABLE_ACTIVITY_LOG': {'env': 'ENABLE_ACTIVITY_LOG', 'default': False},

    # WebDAV root directory
    'WEBDAV_ROOT': {'env': 'WEBDAV_ROOT', 'default': WEBDAV_DIR},

    # Default format priority
    'DEFAULT_FORMAT_PRIORITY': {'env': 'DEFAULT_FORMAT_PRIORITY', 'default': 'azw3,mobi,epub,fb2,txt,pdf'},

    # SMTP (Mail sending) settings
    'SMTP_SERVER': {'env': 'SMTP_SERVER', 'default': ''},
    'SMTP_PORT': {'env': 'SMTP_PORT', 'default': 587},
    'SMTP_USERNAME': {'env': 'SMTP_USERNAME', 'default': ''},
    'SMTP_PASSWORD': {'env': 'SMTP_PASSWORD', 'default': ''},
    'SMTP_ENCRYPTION': {'env': 'SMTP_ENCRYPTION', 'default': 'ssl'}, # 'ssl', 'starttls', or 'none'

    # Registration settings
    'REQUIRE_INVITE_CODE': {'env': 'REQUIRE_INVITE_CODE', 'default': True},
    'DISABLE_NORMAL_USER_UPLOAD': {'env': 'DISABLE_NORMAL_USER_UPLOAD', 'default': False},

    # Text-to-Speech (TTS) settings for Audiobook Generation
    'DEFAULT_TTS_PROVIDER': {'env': 'DEFAULT_TTS_PROVIDER', 'default': 'edge'},
    'DEFAULT_TTS_VOICE': {'env': 'DEFAULT_TTS_VOICE', 'default': 'zh-CN-YunjianNeural'},
    'DEFAULT_TTS_API_KEY': {'env': 'DEFAULT_TTS_API_KEY', 'default': ''},
    'DEFAULT_TTS_BASE_URL': {'env': 'DEFAULT_TTS_BASE_URL', 'default': ''},
    'DEFAULT_TTS_MODEL': {'env': 'DEFAULT_TTS_MODEL', 'default': ''},
    'DEFAULT_TTS_RATE': {'env': 'DEFAULT_TTS_RATE', 'default': '+40%'},
    'DEFAULT_TTS_VOLUME': {'env': 'DEFAULT_TTS_VOLUME', 'default': '+0%'},
    'DEFAULT_TTS_PITCH': {'env': 'DEFAULT_TTS_PITCH', 'default': '+0Hz'},
    'DEFAULT_TTS_SENTENCE_PAUSE': {'env': 'DEFAULT_TTS_SENTENCE_PAUSE', 'default': 650},
    'DEFAULT_TTS_PARAGRAPH_PAUSE': {'env': 'DEFAULT_TTS_PARAGRAPH_PAUSE', 'default': 900},
 
     # Audiobook file cleanup settings
     'AUDIOBOOK_CLEANUP_DAYS': {'env': 'AUDIOBOOK_CLEANUP_DAYS', 'default': 7}, # 0 means do not clean up

    # Large Language Model (LLM) settings for MCP
    'DEFAULT_LLM_PROVIDER': {'env': 'DEFAULT_LLM_PROVIDER', 'default': 'openai'},
    'DEFAULT_LLM_API_KEY': {'env': 'DEFAULT_LLM_API_KEY', 'default': ''},
    'DEFAULT_LLM_BASE_URL': {'env': 'DEFAULT_LLM_BASE_URL', 'default': 'https://api.openai.com/v1'},
    'DEFAULT_LLM_MODEL': {'env': 'DEFAULT_LLM_MODEL', 'default': 'gpt-4o'},
}

# Initialize config as a dictionary first to avoid NameError during initial load
class ConfigManager:
    def __init__(self):
        self._config = {}
        self.load_config()

    def load_config(self):
        """
        Loads the global configuration.
        Priority: Config file > Environment variables > Default values
        """
        os.makedirs(CONFIG_DIR, exist_ok=True)

        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_from_file = json.load(f)
            except (json.JSONDecodeError, IOError):
                config_from_file = {}
        else:
            config_from_file = {}

        loaded_config = {}
        for key, values in DEFAULT_CONFIG.items():
            # Priority 1: Config file
            if key in config_from_file:
                loaded_config[key] = config_from_file[key]
            # Priority 2: Environment variables
            elif os.environ.get(values['env']):
                val = os.environ.get(values['env'])
                if key in ['LOGIN_MAX_ATTEMPTS', 'SESSION_LIFETIME_DAYS', 'SMTP_PORT', 'AUDIOBOOK_CLEANUP_DAYS', 'DEFAULT_TTS_SENTENCE_PAUSE', 'DEFAULT_TTS_PARAGRAPH_PAUSE', 'TALEBOOK_TIMEOUT']:
                    try:
                        loaded_config[key] = int(val)
                    except (ValueError, TypeError):
                        loaded_config[key] = values['default']
                elif key in ['REQUIRE_INVITE_CODE', 'DISABLE_NORMAL_USER_UPLOAD', 'CALIBRE_ADD_DUPLICATES', 'ENABLE_ACTIVITY_LOG', 'TALEBOOK_VERIFY_SSL']:
                    # Handle boolean values from environment variables
                    loaded_config[key] = val.lower() in ('true', '1', 'yes', 'on')
                else:
                    loaded_config[key] = val
            # Priority 3: Default values
            else:
                loaded_config[key] = values['default']
                
        # Ensure SECRET_KEY always exists and is valid
        if not loaded_config.get('SECRET_KEY'):
            loaded_config['SECRET_KEY'] = os.urandom(24).hex()
            # Save immediately to persist the key
            self.save_config({'SECRET_KEY': loaded_config['SECRET_KEY']})
        
        self._config = loaded_config

    def get(self, key, default=None):
        self.load_config()
        return self._config.get(key, default)

    def __getitem__(self, key):
        self.load_config()
        return self._config[key]

    def get_all(self):
        """Returns a copy of the entire configuration dictionary."""
        self.load_config()
        return self._config.copy()

    def save_config(self, new_config):
        """
        Saves the global configuration to a file and triggers a reload of Gunicorn workers.
        """
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        current_config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        for key, value in new_config.items():
            if key in DEFAULT_CONFIG:
                # Skip empty password fields to avoid clearing them
                if key in ['CALIBRE_PASSWORD', 'SMTP_PASSWORD', 'TALEBOOK_PASSWORD'] and not value:
                    continue

                if key in ['LOGIN_MAX_ATTEMPTS', 'SESSION_LIFETIME_DAYS', 'SMTP_PORT', 'AUDIOBOOK_CLEANUP_DAYS', 'DEFAULT_TTS_SENTENCE_PAUSE', 'DEFAULT_TTS_PARAGRAPH_PAUSE', 'TALEBOOK_TIMEOUT'] and value is not None:
                    try:
                        current_config[key] = int(value)
                    except (ValueError, TypeError):
                        pass
                elif key == 'SMTP_ENCRYPTION':
                    current_config[key] = value.lower() if value in ['ssl', 'starttls', 'none'] else 'starttls'
                else:
                    current_config[key] = value

        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
            
            # Signal Gunicorn to reload workers gracefully
            if os.path.exists(GUNICORN_PID_FILE):
                try:
                    with open(GUNICORN_PID_FILE, 'r') as f:
                        pid = int(f.read().strip())
                    logging.info(f"Found Gunicorn PID {pid}. Sending SIGHUP to reload workers.")
                    os.kill(pid, signal.SIGHUP)
                except (IOError, ValueError, ProcessLookupError) as e:
                    logging.warning(f"Could not signal Gunicorn to reload: {e}")
            
            # Force-reload the config in the current worker process immediately
            self.load_config()
            
            return True, "Global configuration saved successfully. Workers are reloading."
        except IOError as e:
            return False, f"Failed to save config file: {e}"

# Load the configuration when the module is loaded
config = ConfigManager()