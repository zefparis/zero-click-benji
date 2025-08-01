import unittest
import logging
from unittest.mock import patch
from core.networking.proxy_chain_manager import ProxyChainManager
from core.utils.logger import setup_logger
import requests  # Import the requests module

class TestProxyChainManager(unittest.TestCase):

    def setUp(self):
        self.logger = setup_logger(__name__, level=logging.CRITICAL) # Reduce logging during tests
        self.proxy_manager = ProxyChainManager(self.logger)

    def test_add_proxy(self):
        self.proxy_manager.add_proxy("socks5", "127.0.0.1:9050")
        self.assertIn("127.0.0.1:9050", self.proxy_manager.proxies["socks5"])
        self.proxy_manager.add_proxy("http", "192.168.1.100:8080")
        self.assertIn("192.168.1.100:8080", self.proxy_manager.proxies["http"])
        self.proxy_manager.add_proxy("invalid", "test")
        self.assertEqual(self.proxy_manager.get_proxies("invalid"), [])

    def test_remove_proxy(self):
        self.proxy_manager.add_proxy("socks5", "127.0.0.1:9050")
        self.proxy_manager.remove_proxy("socks5", "127.0.0.1:9050")
        self.assertNotIn("127.0.0.1:9050", self.proxy_manager.proxies["socks5"])
        self.proxy_manager.remove_proxy("socks5", "nonexistent")
        self.assertEqual(len(self.proxy_manager.get_proxies("socks5")), 0)

    def test_get_proxies(self):
        self.proxy_manager.add_proxy("socks5", "127.0.0.1:9050")
        self.proxy_manager.add_proxy("socks5", "127.0.0.1:9051")
        proxies = self.proxy_manager.get_proxies("socks5")
        self.assertEqual(len(proxies), 2)
        self.assertIn("127.0.0.1:9050", proxies)
        self.assertIn("127.0.0.1:9051", proxies)
        self.assertEqual(self.proxy_manager.get_proxies("invalid"), [])

    def test_set_proxy(self):
        self.proxy_manager.add_proxy("socks5", "127.0.0.1:9050")
        self.proxy_manager.set_proxy("socks5", "127.0.0.1:9050")
        self.assertEqual(self.proxy_manager.current_proxy, "127.0.0.1:9050")
        self.assertEqual(self.proxy_manager.proxy_type, "socks5")
        self.proxy_manager.set_proxy("socks5", "nonexistent")
        self.assertEqual(self.proxy_manager.current_proxy, "127.0.0.1:9050")

    def test_clear_proxy(self):
        self.proxy_manager.add_proxy("socks5", "127.0.0.1:9050")
        self.proxy_manager.set_proxy("socks5", "127.0.0.1:9050")
        self.proxy_manager.clear_proxy()
        self.assertIsNone(self.proxy_manager.current_proxy)
        self.assertIsNone(self.proxy_manager.proxy_type)
        self.assertEqual(len(self.proxy_manager.session.proxies), 0)

    def test_get_current_proxy(self):
        self.proxy_manager.add_proxy("socks5", "127.0.0.1:9050")
        self.proxy_manager.set_proxy("socks5", "127.0.0.1:9050")
        current_proxy = self.proxy_manager.get_current_proxy()
        self.assertEqual(current_proxy, {"type": "socks5", "address": "127.0.0.1:9050"})
        self.proxy_manager.clear_proxy()
        self.assertIsNone(self.proxy_manager.get_current_proxy())

    def test_enable_disable_proxy_rotation(self):
        self.proxy_manager.add_proxy("socks5", "127.0.0.1:9050")  # Add a proxy
        self.proxy_manager.enable_proxy_rotation(interval=10)
        self.assertTrue(self.proxy_manager.proxy_rotation_enabled)
        self.assertEqual(self.proxy_manager.rotation_interval, 10)
        self.proxy_manager.disable_proxy_rotation()
        self.assertFalse(self.proxy_manager.proxy_rotation_enabled)

    def test_test_proxy(self):
        # This test requires a working internet connection and a proxy server
        # For now, we'll just test that it doesn't raise an exception
        self.proxy_manager.add_proxy("http", "127.0.0.1:8080") # Replace with a valid proxy for a real test
        self.proxy_manager.set_proxy("http", "127.0.0.1:8080")
        with patch('requests.sessions.Session.get') as mock_get:
            mock_get.return_value.raise_for_status = lambda: None  # Mock successful response
            self.assertTrue(self.proxy_manager.test_proxy(url="https://www.google.com", timeout=1))

        self.proxy_manager.clear_proxy()
        self.assertFalse(self.proxy_manager.test_proxy())

    def test_get_session(self):
        self.assertIsInstance(self.proxy_manager.get_session(), requests.Session)

if __name__ == '__main__':
    unittest.main()
