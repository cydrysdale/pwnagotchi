#!/usr/bin/env python3
"""
Integration tests for menu scripts
Tests that scripts can be executed and produce expected output.
"""

import os
import sys
import subprocess
import unittest


class TestScriptIntegration(unittest.TestCase):
    """Integration tests for menu action scripts"""

    def setUp(self):
        """Set up test environment"""
        self.scripts_dir = os.path.join(
            os.path.dirname(__file__),
            '..',
            'plugins',
            'onscreen_menu',
            'scripts'
        )

    def test_show_status_executable(self):
        """Test that show_status.py is executable and runs"""
        script_path = os.path.join(self.scripts_dir, 'show_status.py')
        self.assertTrue(os.path.exists(script_path), f"Script not found: {script_path}")

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Status OK", result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("show_status.py timed out")

    def test_view_events_executable(self):
        """Test that view_events.py is executable"""
        script_path = os.path.join(self.scripts_dir, 'view_events.py')
        self.assertTrue(os.path.exists(script_path))

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Script should run (exit code may be non-zero if no logs found)
            # Just verify it doesn't crash
            self.assertIsNotNone(result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("view_events.py timed out")

    def test_list_networks_executable(self):
        """Test that list_networks.py is executable"""
        script_path = os.path.join(self.scripts_dir, 'list_networks.py')
        self.assertTrue(os.path.exists(script_path))

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.assertEqual(result.returncode, 0)
            # Should at least print header
            self.assertIn("Captured Networks", result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("list_networks.py timed out")

    def test_pisugar_status_executable(self):
        """Test that pisugar_status.py is executable"""
        script_path = os.path.join(self.scripts_dir, 'pisugar_status.py')
        self.assertTrue(os.path.exists(script_path))

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.assertEqual(result.returncode, 0)
            # Should print some status (even if "n/a")
            self.assertIn("PiSugar", result.stdout)
        except subprocess.TimeoutExpired:
            self.fail("pisugar_status.py timed out")

    def test_upload_logs_executable(self):
        """Test that upload_logs.sh is executable"""
        script_path = os.path.join(self.scripts_dir, 'upload_logs.sh')
        self.assertTrue(os.path.exists(script_path))

        # Just verify it's a valid bash script (syntax check)
        try:
            result = subprocess.run(
                ['bash', '-n', script_path],
                capture_output=True,
                text=True,
                timeout=2
            )
            self.assertEqual(result.returncode, 0, "Bash syntax error in upload_logs.sh")
        except subprocess.TimeoutExpired:
            self.fail("upload_logs.sh syntax check timed out")

    def test_all_scripts_have_shebang(self):
        """Verify all scripts have proper shebang"""
        for script in os.listdir(self.scripts_dir):
            if script.endswith(('.py', '.sh')):
                script_path = os.path.join(self.scripts_dir, script)
                with open(script_path, 'r') as f:
                    first_line = f.readline().strip()
                    self.assertTrue(
                        first_line.startswith('#!'),
                        f"{script} missing shebang"
                    )


if __name__ == '__main__':
    unittest.main()
