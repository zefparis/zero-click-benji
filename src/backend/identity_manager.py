import logging
import subprocess
import random
import time
import uuid
import ipaddress
from typing import Dict, Any
import platform

class IdentityManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.original_mac = None
        self.original_ip = None
        self.interface = self._get_default_interface()

    def _get_default_interface(self) -> str:
        """Detects the default network interface."""
        system = platform.system()
        if system == "Linux":
            try:
                result = subprocess.run(["route", "-n"], capture_output=True, text=True, check=True)
                for line in result.stdout.splitlines():
                    if "UG" in line and "0.0.0.0" in line:
                        return line.split()[-1]
            except Exception as e:
                self.logger.error(f"Error detecting default interface: {e}")
                return "eth0"  # Default to eth0 if detection fails
        elif system == "Darwin":
            try:
                result = subprocess.run(["route", "-n", "get", "default"], capture_output=True, text=True, check=True)
                for line in result.stdout.splitlines():
                    if "interface:" in line:
                        return line.split("interface:")[1].strip()
            except Exception as e:
                self.logger.error(f"Error detecting default interface: {e}")
                return "en0"  # Default to en0 if detection fails
        else:
            self.logger.warning(f"Unsupported OS: {system}. Defaulting to eth0.")
            return "eth0"
        return "eth0"

    def get_current_mac(self, interface: str = None) -> str:
        interface = interface or self.interface
        try:
            result = subprocess.run(["ifconfig", interface], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if "ether" in line or "lladdr" in line:
                    parts = line.split("ether" if "ether" in line else "lladdr")
                    if len(parts) > 1:
                        return parts[1].strip().split(" ")[0]
            return None
        except Exception as e:
            self.logger.error(f"Error getting MAC address: {e}")
            return None

    def get_current_ip(self, interface: str = None) -> str:
        interface = interface or self.interface
        try:
            result = subprocess.run(["ifconfig", interface], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if "inet " in line:
                    return line.split("inet ")[1].strip().split(" ")[0]
            return None
        except Exception as e:
            self.logger.error(f"Error getting IP address: {e}")
            return None

    def change_mac_address(self, interface: str = None, new_mac: str = None):
        interface = interface or self.interface
        if not new_mac:
            new_mac = self._generate_random_mac()
        try:
            self.logger.info(f"Changing MAC address on {interface} to {new_mac}")
            subprocess.run(["ifconfig", interface, "down"], check=True)
            subprocess.run(["ifconfig", interface, "hw", "ether", new_mac], check=True)
            subprocess.run(["ifconfig", interface, "up"], check=True)
            self.logger.info(f"MAC address on {interface} changed to {new_mac}")
            return True
        except Exception as e:
            self.logger.error(f"Error changing MAC address: {e}")
            return False

    def restore_mac_address(self, interface: str = None):
        interface = interface or self.interface
        if self.original_mac:
            self.change_mac_address(interface, self.original_mac)
            self.logger.info(f"MAC address on {interface} restored to {self.original_mac}")
        else:
            self.logger.warning("Original MAC address not recorded.")

    def change_ip_address(self, interface: str = None, new_ip: str = None):
        interface = interface or self.interface
        if not new_ip:
            new_ip = self._generate_random_ip()
        try:
            self.logger.info(f"Changing IP address on {interface} to {new_ip}")
            subprocess.run(["ifconfig", interface, "down"], check=True)
            subprocess.run(["ifconfig", interface, "inet", new_ip], check=True)
            subprocess.run(["ifconfig", interface, "up"], check=True)
            self.logger.info(f"IP address on {interface} changed to {new_ip}")
            return True
        except Exception as e:
            self.logger.error(f"Error changing IP address: {e}")
            return False

    def restore_ip_address(self, interface: str = None):
        interface = interface or self.interface
        if self.original_ip:
            self.change_ip_address(interface, self.original_ip)
            self.logger.info(f"IP address on {interface} restored to {self.original_ip}")
        else:
            self.logger.warning("Original IP address not recorded.")

    def _generate_random_mac(self) -> str:
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def _generate_random_ip(self) -> str:
        while True:
            ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            try:
                ipaddress.ip_address(ip)
                return ip
            except ValueError:
                continue

    def start_tor_session(self, data: Dict[str, Any] = None):
        self.logger.info(f"Starting Tor session - Data: {data}")
        self.original_mac = self.get_current_mac()
        self.original_ip = self.get_current_ip()
        self.change_mac_address()
        self.change_ip_address()
        time.sleep(random.uniform(2, 5))
        self.logger.info("Tor session started")

    def stop_tor_session(self, data: Dict[str, Any] = None):
        self.logger.info(f"Stopping Tor session - Data: {data}")
        self.restore_mac_address()
        self.restore_ip_address()
        time.sleep(random.uniform(1, 3))
        self.logger.info("Tor session stopped")