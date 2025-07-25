import unittest
import logging
from unittest.mock import patch, MagicMock
import platform
from core.networking.identity_manager import IdentityManager
from core.utils.logger import setup_logger

class TestIdentityManager(unittest.TestCase):

    def setUp(self):
        self.logger = setup_logger(__name__, level=logging.CRITICAL)
        self.identity_manager = IdentityManager(self.logger)

    @patch("subprocess.run")
    def test_get_default_interface_linux(self, mock_run):
        if platform.system() == "Linux":
            mock_run.return_value.stdout = "0.0.0.0         0.0.0.0         0.0.0.0         UG    0      0        0 eth0"
            mock_run.return_value.returncode = 0
            interface = self.identity_manager._get_default_interface()
            self.assertEqual(interface, "eth0")

    @patch("subprocess.run")
    def test_get_default_interface_darwin(self, mock_run):
        if platform.system() == "Darwin":
            mock_run.return_value.stdout = "interface: en0"
            mock_run.return_value.returncode = 0
            interface = self.identity_manager._get_default_interface()
            self.assertEqual(interface, "en0")

    @patch("subprocess.run")
    def test_get_default_interface_unsupported(self, mock_run):
        if platform.system() not in ["Linux", "Darwin"]:
            interface = self.identity_manager._get_default_interface()
            self.assertEqual(interface, "eth0")

    @patch("subprocess.run")
    def test_get_current_mac(self, mock_run):
        mock_run.return_value.stdout = "        ether 00:11:22:33:44:55 "
        mock_run.return_value.returncode = 0
        mac = self.identity_manager.get_current_mac()
        self.assertEqual(mac, "00:11:22:33:44:55")

        mock_run.return_value.stdout = "        lladdr 00:11:22:33:44:55 "
        mock_run.return_value.returncode = 0
        mac = self.identity_manager.get_current_mac()
        self.assertEqual(mac, "00:11:22:33:44:55")

        mock_run.return_value.stdout = "        invalid output "
        mock_run.return_value.returncode = 0
        mac = self.identity_manager.get_current_mac()
        self.assertIsNone(mac)

        mock_run.side_effect = Exception("Test Exception")
        mac = self.identity_manager.get_current_mac()
        self.assertIsNone(mac)

    @patch("subprocess.run")
    def test_get_current_ip(self, mock_run):
        mock_run.return_value.stdout = "        inet 192.168.1.100 "
        mock_run.return_value.returncode = 0
        ip = self.identity_manager.get_current_ip()
        self.assertEqual(ip, "192.168.1.100")

        mock_run.return_value.stdout = "        invalid output "
        mock_run.return_value.returncode = 0
        ip = self.identity_manager.get_current_ip()
        self.assertIsNone(ip)

        mock_run.side_effect = Exception("Test Exception")
        ip = self.identity_manager.get_current_ip()
        self.assertIsNone(ip)

    @patch("subprocess.run")
    def test_change_mac_address(self, mock_run):
        mock_run.return_value.returncode = 0
        result = self.identity_manager.change_mac_address(new_mac="00:AA:BB:CC:DD:EE")
        self.assertTrue(result)
        mock_run.side_effect = Exception("Test Exception")
        result = self.identity_manager.change_mac_address(new_mac="00:AA:BB:CC:DD:EE")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_restore_mac_address(self, mock_run):
        self.identity_manager.original_mac = "00:11:22:33:44:55"
        mock_run.return_value.returncode = 0
        self.identity_manager.restore_mac_address()
        self.assertTrue(mock_run.called)

        self.identity_manager.original_mac = None
        self.identity_manager.restore_mac_address()
        self.assertFalse(mock_run.called)

    @patch("subprocess.run")
    def test_change_ip_address(self, mock_run):
        mock_run.return_value.returncode = 0
        result = self.identity_manager.change_ip_address(new_ip="192.168.1.200")
        self.assertTrue(result)
        mock_run.side_effect = Exception("Test Exception")
        result = self.identity_manager.change_ip_address(new_ip="192.168.1.200")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_restore_ip_address(self, mock_run):
        self.identity_manager.original_ip = "192.168.1.100"
        mock_run.return_value.returncode = 0
        self.identity_manager.restore_ip_address()
        self.assertTrue(mock_run.called)

        self.identity_manager.original_ip = None
        self.identity_manager.restore_ip_address()
        self.assertFalse(mock_run.called)

    def test_start_tor_session(self):
        with patch.object(self.identity_manager, 'get_current_mac', return_value="00:11:22:33:44:55"):
            with patch.object(self.identity_manager, 'get_current_ip', return_value="192.168.1.100"):
                with patch.object(self.identity_manager, 'change_mac_address', return_value=True):
                    with patch.object(self.identity_manager, 'change_ip_address', return_value=True):
                        self.identity_manager.start_tor_session()
                        self.assertEqual(self.identity_manager.original_mac, "00:11:22:33:44:55")
                        self.assertEqual(self.identity_manager.original_ip, "192.168.1.100")

    def test_stop_tor_session(self):
        with patch.object(self.identity_manager, 'restore_mac_address', return_value=True):
            with patch.object(self.identity_manager, 'restore_ip_address', return_value=True):
                self.identity_manager.stop_tor_session()
                self.assertTrue(self.identity_manager.restore_mac_address.called)
                self.assertTrue(self.identity_manager.restore_ip_address.called)

if __name__ == '__main__':
    unittest.main()
