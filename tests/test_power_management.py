import unittest
from unittest.mock import patch, mock_open, MagicMock
import platform
import os
from core.power import PowerPlanManager

class TestPowerPlanManager(unittest.TestCase):

    def setUp(self):
        self.manager = PowerPlanManager()

    @patch('platform.system')
    def test_enter_non_linux_windows(self, mock_system):
        mock_system.return_value = "Darwin" # MacOS
        manager = PowerPlanManager()
        # Should just log a warning and not crash
        with manager:
            pass

    @patch('platform.system')
    @patch('glob.glob')
    @patch('builtins.open', new_callable=mock_open, read_data='powersave')
    def test_enter_linux_success(self, mock_file, mock_glob, mock_system):
        mock_system.return_value = "Linux"
        mock_glob.return_value = ['/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor']
        
        manager = PowerPlanManager()
        manager.is_linux = True
        manager.is_windows = False

        # Configure mock to change return value after first write?
        # Easier to just rely on the fact that we confirmed enter logic works,
        # and for exit logic, we can manually manipulate the mock read if needed.
        # But here, since mock read always returns 'powersave', the exit logic sees
        # current='powersave', original='powersave', so it does NOTHING.
        
        # To test restoration, we need the read in __exit__ to return something else (e.g. 'performance')
        
        # Side effect for open:
        # 1. Enter: read -> 'powersave'
        # 2. Enter: write 'performance'
        # 3. Exit: read -> 'performance'
        # 4. Exit: write 'powersave'

        # Let's use side_effect on the file object's read method
        handlers = (
            mock_file.return_value.read.side_effect
        ) = ['powersave', 'performance']

        with manager:
            # Check if it tried to read the original governor
            mock_file.assert_any_call('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r')
            # Check if it tried to write 'performance'
            mock_file.assert_any_call('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'w')
            mock_file().write.assert_any_call('performance')
            
        # Check restoration on exit
        # It should try to write back the original value ('powersave')
        mock_file().write.assert_called_with('powersave')

    @patch('platform.system')
    @patch('glob.glob')
    def test_enter_linux_permission_error(self, mock_glob, mock_system):
        mock_system.return_value = "Linux"
        mock_glob.return_value = ['/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor']
        
        # Mock open to raise PermissionError on write
        m = mock_open(read_data='powersave')
        m.side_effect = [m.return_value, PermissionError("Denied")] 
        # First call is read (success), second is write (fail) - complex to mock side_effect on calls nicely with mock_open
        # Simplified approach: mock the file object's write method to raise exception? 
        # Or just mock open to succeed on read, fail on write.
        
        with patch('builtins.open', m):
            # We need to manually control the read vs write behavior for the mock
            # Because side_effect on the mock_open object itself applies to the open() call
            
            # Let's just simulate open failing for write for simplicity in this specific test structure
            # or use a more robust side_effect for open
            
            def open_side_effect(file, mode='r'):
                if 'w' in mode:
                    raise PermissionError("Access denied")
                return MagicMock(read=MagicMock(return_value='powersave'))

            m.side_effect = open_side_effect

            manager = PowerPlanManager()
            manager.is_linux = True
            
            # Should not crash
            with manager:
                pass

    @patch('platform.system')
    @patch('glob.glob')
    @patch('builtins.open', new_callable=mock_open, read_data='performance')
    def test_enter_linux_already_performance(self, mock_file, mock_glob, mock_system):
        mock_system.return_value = "Linux"
        mock_glob.return_value = ['/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor']
        
        manager = PowerPlanManager()
        manager.is_linux = True
        
        with manager:
            # Should read
            mock_file.assert_any_call('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor', 'r')
            # Should NOT write because it's already performance
            assert mock_file().write.call_count == 0

if __name__ == '__main__':
    unittest.main()