import os
import tempfile
import unittest
from unittest import mock

import config


class EmailConfigTests(unittest.TestCase):
    def test_update_email_alert_settings_persists_sender_and_recipients(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, 'app_config.json')
            with mock.patch.object(config, 'APP_CONFIG_PATH', temp_path):
                config.ensure_config_files()

                updated = config.update_email_alert_settings({
                    'enabled': True,
                    'smtp_host': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'use_tls': True,
                    'username': 'sender@example.com',
                    'password': 'secret',
                    'sender': 'sender@example.com',
                    'recipients': ['admin@example.com', 'ops@example.com']
                })

                self.assertTrue(updated['enabled'])
                self.assertEqual(updated['sender'], 'sender@example.com')
                self.assertEqual(updated['recipients'], ['admin@example.com', 'ops@example.com'])
                self.assertEqual(config.get_email_config()['sender'], 'sender@example.com')
                self.assertEqual(config.get_email_config()['recipients'], ['admin@example.com', 'ops@example.com'])


if __name__ == '__main__':
    unittest.main()
