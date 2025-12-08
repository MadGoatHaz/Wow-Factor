import shutil
import platform
import logging
import subprocess
import sys

def check_gamemode():
    """
    Checks if 'gamemoded' is available on Linux.
    If not, suggests installation commands based on the package manager.
    """
    if platform.system() != "Linux":
        return

    if shutil.which("gamemoded"):
        logging.info("GameMode daemon (gamemoded) detected.")
        return

    logging.warning("GameMode daemon (gamemoded) not found.")
    
    # Detect package manager
    pkg_managers = {
        "apt": "sudo apt install gamemode",
        "dnf": "sudo dnf install gamemode",
        "pacman": "sudo pacman -S gamemode",
        "zypper": "sudo zypper install gamemode",
    }
    
    install_cmd = None
    for pm, cmd in pkg_managers.items():
        if shutil.which(pm):
            install_cmd = cmd
            break
            
    print("\n" + "!"*80)
    print("MISSING DEPENDENCY: GameMode (gamemoded)")
    print("High-performance mode requires the 'gamemode' package.")
    
    if install_cmd:
        print(f"Detected package manager. You can try installing it with:\n")
        print(f"    {install_cmd}\n")
        
        # Interactive prompt
        try:
            response = input("Would you like to try installing it now? (y/N): ").strip().lower()
            if response == 'y':
                print(f"Executing: {install_cmd}...")
                try:
                    subprocess.check_call(install_cmd.split())
                    print("Installation successful!")
                    return
                except subprocess.CalledProcessError as e:
                    print(f"Installation failed: {e}")
                    print("Please install 'gamemode' manually.")
                except Exception as e:
                     print(f"An error occurred: {e}")
        except EOFError:
            pass # Handle non-interactive environments
            
    else:
        print("Could not detect package manager. Please install 'gamemode' manually.")
        
    print("!"*80 + "\n")
    # Give user a moment to read if they didn't install
    import time
    time.sleep(2)