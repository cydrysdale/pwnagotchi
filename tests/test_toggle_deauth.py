#!/usr/bin/env python3
"""
Unit tests for toggle_deauth.py script
Tests state toggling and audit trail functionality.
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock, call

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'onscreen_menu', 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'onscreen_menu'))


class TestToggleDeauth(unittest.TestCase):
    """Test toggle_deauth script functionality"""

    @patch('toggle_deauth.write_deauth_state')
    @patch('toggle_deauth.read_deauth_state')
    @patch('toggle_deauth.audit')
    @patch('toggle_deauth.notify_agent')
    @patch('os.path.exists')
    def test_toggle_from_disabled_to_enabled(self, mock_exists, mock_notify,
                                             mock_audit, mock_read, mock_write):
        """Test toggling deauth from disabled to enabled"""
        # Setup mocks
        mock_read.return_value = False  # Currently disabled
        mock_write.return_value = True
        mock_exists.return_value = True  # Allow file exists
        mock_notify.return_value = (True, None)
        mock_audit.return_value = True

        # Import and run main
        from toggle_deauth import main

        with patch('builtins.print') as mock_print:
            main()

        # Verify state was toggled to enabled
        mock_write.assert_called_once_with(True)

        # Verify audit was called
        mock_audit.assert_called_once()
        audit_call = mock_audit.call_args[0][0]
        self.assertEqual(audit_call["action"], "arm")

        # Verify print output
        mock_print.assert_called()
        print_args = [call[0][0] for call in mock_print.call_args_list]
        self.assertTrue(any("ARMED" in arg for arg in print_args))

    @patch('toggle_deauth.write_deauth_state')
    @patch('toggle_deauth.read_deauth_state')
    @patch('toggle_deauth.audit')
    @patch('toggle_deauth.notify_agent')
    @patch('os.path.exists')
    def test_toggle_from_enabled_to_disabled(self, mock_exists, mock_notify,
                                             mock_audit, mock_read, mock_write):
        """Test toggling deauth from enabled to disabled"""
        # Setup mocks
        mock_read.return_value = True  # Currently enabled
        mock_write.return_value = True
        mock_exists.return_value = True
        mock_notify.return_value = (True, None)
        mock_audit.return_value = True

        from toggle_deauth import main

        with patch('builtins.print') as mock_print:
            main()

        # Verify state was toggled to disabled
        mock_write.assert_called_once_with(False)

        # Verify audit entry
        audit_call = mock_audit.call_args[0][0]
        self.assertEqual(audit_call["action"], "disarm")

    @patch('toggle_deauth.write_deauth_state')
    @patch('toggle_deauth.read_deauth_state')
    @patch('toggle_deauth.audit')
    @patch('os.path.exists')
    def test_toggle_without_allow_file(self, mock_exists, mock_audit,
                                       mock_read, mock_write):
        """Test toggle when allow file is missing"""
        mock_read.return_value = False
        mock_write.return_value = True
        mock_exists.return_value = False  # No allow file
        mock_audit.return_value = True

        from toggle_deauth import main

        with patch('builtins.print'):
            main()

        # Verify audit shows agent was not notified
        audit_call = mock_audit.call_args[0][0]
        self.assertFalse(audit_call["agent_notify"])
        self.assertEqual(audit_call["agent_error"], "allow-file-missing")

    @patch('toggle_deauth.write_deauth_state')
    @patch('toggle_deauth.read_deauth_state')
    def test_toggle_write_failure(self, mock_read, mock_write):
        """Test handling of write failures"""
        mock_read.return_value = False
        mock_write.return_value = False  # Write fails

        from toggle_deauth import main

        with patch('builtins.print') as mock_print:
            main()

        # Verify error message printed
        error_printed = any("ERROR" in str(call) for call in mock_print.call_args_list)
        self.assertTrue(error_printed)


if __name__ == '__main__':
    unittest.main()
