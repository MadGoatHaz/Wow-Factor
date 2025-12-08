import os
import sys
import glob
import logging
import platform
import subprocess

logger = logging.getLogger(__name__)

class PowerPlanManager:
    """
    Context manager to handle system power plans/CPU governors.
    Focuses on switching to 'performance' mode during critical operations
    and restoring the previous state afterwards.
    """

    def __init__(self):
        self.original_governors = {}
        self.is_linux = platform.system() == "Linux"
        self.is_windows = platform.system() == "Windows"
        self.gamemode_active = False

    def __enter__(self):
        """
        Save current state and attempt to switch to high performance.
        """
        logger.info("Entering PowerPlanManager context...")
        if self.is_linux:
            self._enter_linux()
        elif self.is_windows:
            self._enter_windows()
        else:
            logger.warning(f"Power management not implemented for platform: {platform.system()}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Restore original state.
        """
        logger.info("Exiting PowerPlanManager context...")
        if self.is_linux:
            self._exit_linux()
        elif self.is_windows:
            self._exit_windows()

    def _enter_linux(self):
        """
        Linux implementation: Attempt to Request GameMode and set CPU governors to 'performance'.
        """
        # Try GameMode first (user-space friendly)
        self._manage_gamemode_linux(enable=True)

        # Then try direct sysfs manipulation (requires root)
        cpu_freq_path = "/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"
        governor_files = glob.glob(cpu_freq_path)

        if not governor_files:
            # If we successfully activated gamemode, this isn't as critical, so just debug log
            log_level = logging.INFO if self.gamemode_active else logging.WARNING
            logger.log(log_level, "No CPU frequency scaling governor files found.")
            return

        success_count = 0
        total_count = len(governor_files)
        permission_error_logged = False

        for gov_file in governor_files:
            try:
                # Save original governor
                try:
                    with open(gov_file, 'r') as f:
                        original = f.read().strip()
                except IOError as e:
                    logger.debug(f"Could not read governor for {gov_file}: {e}")
                    continue
                
                self.original_governors[gov_file] = original

                # detailed check if we are already on performance
                if original == 'performance':
                    success_count += 1
                    continue

                # Try to set to performance
                # Note: This usually requires root privileges.
                with open(gov_file, 'w') as f:
                    f.write('performance')
                
                success_count += 1
                
            except PermissionError:
                # Expected if not running as root
                # We log once as warning then debug to avoid spam
                if not permission_error_logged:
                    logger.warning(f"Permission denied modifying CPU governors. Run as root for automatic CPU performance switching.")
                    permission_error_logged = True
            except Exception as e:
                logger.error(f"Error handling governor for {gov_file}: {e}")

        if success_count > 0:
            if success_count == total_count:
                logger.info(f"Set all {success_count} CPUs to performance mode.")
            else:
                logger.info(f"Set {success_count}/{total_count} CPUs to performance mode.")
        elif not permission_error_logged:
            logger.info("Could not set CPUs to performance mode. Proceeding with current settings.")

    def _exit_linux(self):
        """
        Linux implementation: Restore original governors and release GameMode.
        """
        # Release GameMode
        self._manage_gamemode_linux(enable=False)

        if not self.original_governors:
            return

        restored_count = 0
        for gov_file, original_gov in self.original_governors.items():
            try:
                # Check if current is different before writing to avoid unnecessary I/O
                current = None
                try:
                    with open(gov_file, 'r') as f:
                        current = f.read().strip()
                except Exception:
                    pass
                
                if current != original_gov:
                    with open(gov_file, 'w') as f:
                        f.write(original_gov)
                    restored_count += 1
            except PermissionError:
                pass # If we failed to set it, we likely fail to restore it silently
            except Exception as e:
                logger.error(f"Failed to restore governor for {gov_file}: {e}")

        if restored_count > 0:
            logger.info(f"Restored CPU governors for {restored_count} CPUs.")

    def _manage_gamemode_linux(self, enable: bool):
        """
        Interact with Feral Interactive's GameMode daemon via DBus.
        """
        try:
            # Check if dbus-send exists
            subprocess.run(["which", "dbus-send"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            method = "RegisterGame" if enable else "UnregisterGame"
            pid = os.getpid()
            
            # dbus-send --session --type=method_call --print-reply --dest=com.feralinteractive.GameMode /com/feralinteractive/GameMode com.feralinteractive.GameMode.RegisterGame int32:<pid>
            cmd = [
                "dbus-send", "--session", "--type=method_call", "--print-reply",
                "--dest=com.feralinteractive.GameMode",
                "/com/feralinteractive/GameMode",
                f"com.feralinteractive.GameMode.{method}",
                f"int32:{pid}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if enable:
                    self.gamemode_active = True
                    logger.info(f"GameMode activated successfully (PID: {pid}).")
                else:
                    self.gamemode_active = False
                    logger.info(f"GameMode deactivated successfully (PID: {pid}).")
            else:
                # It's common for this to fail if gamemoded isn't installed or running, so we just debug log failure
                # unless we were explicitly trying to disable it and it failed
                level = logging.ERROR if (not enable and self.gamemode_active) else logging.DEBUG
                logger.log(level, f"GameMode DBus call failed: {result.stderr.strip()}")

        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.debug("dbus-send not found or failed, skipping GameMode integration.")
        except Exception as e:
            logger.debug(f"Unexpected error managing GameMode: {e}")

    def _enter_windows(self):
        """
        Windows implementation placeholder.
        Would use 'powercfg' commands.
        """
        logger.debug("Windows power management not yet implemented.")

    def _exit_windows(self):
        """
        Windows implementation placeholder.
        """
        pass