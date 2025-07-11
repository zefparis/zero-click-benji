import logging
import uuid
from typing import List, Dict, Any

class BotnetManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.botnets = {}  # {botnet_id: {name: str, devices: [device_id]}}
        self.devices = {}  # {device_id: {botnet_id: str, status: str, last_seen: timestamp}}

    def create_botnet(self, name: str) -> str:
        botnet_id = str(uuid.uuid4())
        self.botnets[botnet_id] = {"name": name, "devices": []}
        self.logger.info(f"Botnet created: {name} (ID: {botnet_id})")
        return botnet_id

    def manage_botnet_devices(self, botnet_id: str, action: str, device_id: str = None):
        if botnet_id not in self.botnets:
            self.logger.warning(f"Botnet not found: {botnet_id}")
            return

        if action == "add":
            if device_id is None:
                device_id = str(uuid.uuid4())
            self.botnets[botnet_id]["devices"].append(device_id)
            self.devices[device_id] = {"botnet_id": botnet_id, "status": "online", "last_seen": None}
            self.logger.info(f"Device {device_id} added to botnet {botnet_id}")
        elif action == "remove":
            if device_id in self.botnets[botnet_id]["devices"]:
                self.botnets[botnet_id]["devices"].remove(device_id)
                del self.devices[device_id]
                self.logger.info(f"Device {device_id} removed from botnet {botnet_id}")
            else:
                self.logger.warning(f"Device {device_id} not found in botnet {botnet_id}")
        else:
            self.logger.warning(f"Invalid action: {action}")

    def control_botnet_devices(self, botnet_id: str, command: str, device_id: str = None):
        if botnet_id not in self.botnets:
            self.logger.warning(f"Botnet not found: {botnet_id}")
            return

        if device_id:
            if device_id in self.devices and self.devices[device_id]["botnet_id"] == botnet_id:
                self.logger.info(f"Sending command '{command}' to device {device_id} in botnet {botnet_id}")
                # Placeholder for sending command to device
            else:
                self.logger.warning(f"Device {device_id} not found in botnet {botnet_id}")
        else:
            self.logger.info(f"Sending command '{command}' to all devices in botnet {botnet_id}")
            # Placeholder for sending command to all devices
    
    def get_botnets(self) -> Dict[str, Dict[str, Any]]:
        return self.botnets

    def get_devices(self) -> Dict[str, Dict[str, Any]]:
        return self.devices