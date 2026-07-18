"""Tests for core/system_deps.py — gamemode detection and package manager discovery.

Covers:
  - Non-Linux early return
  - gamemoded found / not found
  - Package manager detection (apt, dnf, pacman, zypper, none)
  - Interactive install: success, failure, decline, EOFError
  - Print output content
"""
import unittest
from unittest.mock import patch, MagicMock, call
from io import StringIO
import logging
from core.system_deps import check_gamemode


class TestCheckGamemode(unittest.TestCase):
    """Test suite for check_gamemode()."""

    # ---------------------------------------------------------------------
    # Platform guard
    # ---------------------------------------------------------------------

    @patch('platform.system', return_value='Darwin')
    def test_returns_none_on_macos(self, mock_system):
        """check_gamemode() returns None on macOS."""
        result = check_gamemode()
        self.assertIsNone(result)

    @patch('platform.system', return_value='Windows')
    def test_returns_none_on_windows(self, mock_system):
        """check_gamemode() returns None on Windows."""
        result = check_gamemode()
        self.assertIsNone(result)

    # ---------------------------------------------------------------------
    # gamemoded found
    # ---------------------------------------------------------------------

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_returns_none_when_gamemoded_found(self, mock_which, mock_system):
        """check_gamemode() returns None when gamemoded is on PATH."""
        mock_which.return_value = '/usr/bin/gamemoded'
        result = check_gamemode()
        self.assertIsNone(result)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_logs_info_when_gamemoded_found(self, mock_which, mock_system):
        """Info log is emitted when gamemoded is detected."""
        mock_which.return_value = '/usr/bin/gamemoded'
        with patch('core.system_deps.logging.info') as mock_info:
            check_gamemode()
            mock_info.assert_called_once_with(
                "GameMode daemon (gamemoded) detected."
            )

    # ---------------------------------------------------------------------
    # gamemoded not found — logging
    # ---------------------------------------------------------------------

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which', return_value=None)
    def test_logs_warning_when_gamemoded_not_found(self, mock_which, mock_system):
        """Warning log is emitted when gamemoded is missing."""
        with patch('core.system_deps.logging.warning') as mock_warn:
            with patch('builtins.input', side_effect=EOFError):
                check_gamemode()
            mock_warn.assert_called_once_with(
                "GameMode daemon (gamemoded) not found."
            )

    # ---------------------------------------------------------------------
    # Package manager detection
    # ---------------------------------------------------------------------

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_detects_apt_package_manager(self, mock_which, mock_system):
        """apt is detected when present on PATH."""
        def which_side_effect(name):
            if name == 'apt':
                return '/usr/bin/apt'
            return None

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', side_effect=EOFError):
                check_gamemode()

        output = captured.getvalue()
        self.assertIn('apt install gamemode', output)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_detects_pacman_package_manager(self, mock_which, mock_system):
        """pacman is detected when present on PATH."""
        def which_side_effect(name):
            if name == 'pacman':
                return '/usr/bin/pacman'
            return None

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', side_effect=EOFError):
                check_gamemode()

        output = captured.getvalue()
        self.assertIn('pacman -S gamemode', output)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_detects_dnf_package_manager(self, mock_which, mock_system):
        """dnf is detected when present on PATH."""
        def which_side_effect(name):
            if name == 'dnf':
                return '/usr/bin/dnf'
            return None

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', side_effect=EOFError):
                check_gamemode()

        output = captured.getvalue()
        self.assertIn('dnf install gamemode', output)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_detects_zypper_package_manager(self, mock_which, mock_system):
        """zypper is detected when present on PATH."""
        def which_side_effect(name):
            if name == 'zypper':
                return '/usr/bin/zypper'
            return None

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', side_effect=EOFError):
                check_gamemode()

        output = captured.getvalue()
        self.assertIn('zypper install gamemode', output)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which', return_value=None)
    def test_no_package_manager_detected(self, mock_which, mock_system):
        """Manual install message printed when no known PM is found."""
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', side_effect=EOFError):
                check_gamemode()

        output = captured.getvalue()
        self.assertIn('install', output.lower())
        self.assertIn('manually', output)

    # ---------------------------------------------------------------------
    # Interactive install flow
    # ---------------------------------------------------------------------

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_install_success_path(self, mock_which, mock_system):
        """User answers 'y' and subprocess succeeds."""
        def which_side_effect(name):
            if name == 'apt':
                return '/usr/bin/apt'
            return None

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', return_value='y'):
                with patch('subprocess.check_call') as mock_call:
                    check_gamemode()

        mock_call.assert_called_once_with(['sudo', 'apt', 'install', 'gamemode'])
        self.assertIn('Installation successful', captured.getvalue())

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_install_failure_calledprocesserror(self, mock_which, mock_system):
        """User answers 'y' but subprocess raises CalledProcessError."""
        import subprocess

        def which_side_effect(name):
            if name == 'apt':
                return '/usr/bin/apt'
            return None

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', return_value='y'):
                with patch('subprocess.check_call',
                           side_effect=subprocess.CalledProcessError(1, 'apt')):
                    check_gamemode()

        output = captured.getvalue()
        self.assertIn('Installation failed', output)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_user_declines_install(self, mock_which, mock_system):
        """User answers 'n' — no subprocess call made."""
        def which_side_effect(name):
            if name == 'apt':
                return '/usr/bin/apt'
            return None

        mock_which.side_effect = which_side_effect
        with patch('subprocess.check_call') as mock_call:
            with patch('builtins.input', return_value='n'):
                check_gamemode()

        mock_call.assert_not_called()

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_non_interactive_eoferror_handled(self, mock_which, mock_system):
        """EOFError from input() is gracefully caught."""
        def which_side_effect(name):
            if name == 'apt':
                return '/usr/bin/apt'
            return None

        mock_which.side_effect = which_side_effect
        # Should not raise — EOFError is caught inside check_gamemode
        with patch('builtins.input', side_effect=EOFError):
            check_gamemode()

    # ---------------------------------------------------------------------
    # Print output structure
    # ---------------------------------------------------------------------

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_prints_missing_dependency_banner(self, mock_which, mock_system):
        """Output contains the MISSING DEPENDENCY header."""
        def which_side_effect(name):
            if name == 'pacman':
                return '/usr/bin/pacman'
            return None

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', side_effect=EOFError):
                check_gamemode()

        output = captured.getvalue()
        self.assertIn('MISSING DEPENDENCY', output)
        self.assertIn('GameMode', output)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_priority_order_apt_before_pacman(self, mock_which, mock_system):
        """When both apt and pacman exist, apt wins (dict iteration order)."""
        def which_side_effect(name):
            if name == 'gamemoded':
                return None  # gamemoded NOT found, so we proceed to PM detection
            return '/usr/bin/' + name  # all PMs found

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', side_effect=EOFError):
                check_gamemode()

        output = captured.getvalue()
        # apt comes first in the pkg_managers dict iteration order
        self.assertIn('apt install gamemode', output)

    # ---------------------------------------------------------------------
    # Exception during install (generic)
    # ---------------------------------------------------------------------

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_install_generic_exception_handled(self, mock_which, mock_system):
        """A generic exception during install is caught and reported."""
        def which_side_effect(name):
            if name == 'apt':
                return '/usr/bin/apt'
            return None

        mock_which.side_effect = which_side_effect
        captured = StringIO()
        with patch('sys.stdout', captured):
            with patch('builtins.input', return_value='y'):
                with patch('subprocess.check_call',
                           side_effect=RuntimeError('disk full')):
                    check_gamemode()

        output = captured.getvalue()
        self.assertIn('error occurred', output.lower())


if __name__ == '__main__':
    unittest.main()