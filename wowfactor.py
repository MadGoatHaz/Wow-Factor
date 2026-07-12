# wowfactor.py

import sys
import os
import subprocess
import platform
import logging
import shutil

VERSION = "1.1.0"

VENV_DIR = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "wowfactor.log")
REQUIRED_PACKAGES = ["textual", "psutil", "py-cpuinfo", "textual-plotext", "plotext"] # Keeping this list here for direct reference

def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    # Clear existing handlers to prevent duplicate logs if called multiple times or by other modules
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s",
                        handlers=[logging.FileHandler(LOG_FILE, mode='a'), logging.StreamHandler(sys.stdout)])

def check_and_setup_venv_and_launch():
    setup_logging() # Initialize logging for the launcher

    # Ensure requirements.txt is up-to-date for setup
    with open(REQUIREMENTS_FILE, 'w') as f:
        for pkg in REQUIRED_PACKAGES:
            f.write(f"{pkg}\n")

    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), VENV_DIR)
    venv_python_executable = os.path.join(venv_path, "Scripts", "python.exe") if platform.system() == "Windows" else os.path.join(venv_path, "bin", "python")

    # Check if running within a virtual environment
    if sys.prefix == sys.base_prefix:
        logging.info("Not running in a virtual environment. Starting setup...")

        if not os.path.exists(venv_path):
            logging.info(f"Creating virtual environment at {venv_path}...")
            try:
                subprocess.check_call([sys.executable, "-m", "venv", venv_path])
                logging.info("Virtual environment created successfully.")
            except Exception as e:
                logging.critical(f"Fatal: Error creating virtual environment: {e}")
                sys.exit(1)
        else:
            logging.info(f"Virtual environment already exists at {venv_path}.")
        
        logging.info(f"Installing/Updating dependencies from {REQUIREMENTS_FILE}...")
        try:
            subprocess.check_call([venv_python_executable, "-m", "pip", "install", "--upgrade", "-r", REQUIREMENTS_FILE])
            logging.info("Dependencies installed successfully.")
        except Exception as e:
            logging.critical(f"Fatal: An unexpected error occurred during dependency installation: {e}")
            sys.exit(1)

        logging.info("Setup complete. Launching application inside the virtual environment...")
        print("\n" + "="*80 + "\nSETUP COMPLETE. LAUNCHING APPLICATION...\n" + "="*80)
        
        # Re-launch THIS script inside the virtual environment
        try:
            # Use os.execlp to replace the current process with the one in the venv
            # This ensures the correct python interpreter and environment are used
            os.execlp(venv_python_executable, venv_python_executable, os.path.abspath(__file__), *sys.argv[1:])
        except Exception as e:
            logging.critical(f"Fatal: Error re-launching script in virtual environment: {e}")
            sys.exit(1)
    else:
        # Running inside the virtual environment, proceed to launch application
        logging.info("Running in a virtual environment. Launching WowFactor TUI...")

        # Check for system dependencies (e.g. GameMode)
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        try:
            from core.system_deps import check_gamemode
            check_gamemode()
        except ImportError:
            logging.warning("Could not import system dependency checker.")

        try:
            # Ensure Textual can be imported before launching
            import textual
            
            # Import the app class from ui.app
            # We need to make sure the current directory is in sys.path
            # (Already added above)
            from ui.app import WowFactorTUI
            
            # Run the app
            app = WowFactorTUI()
            app.run()
            
        except ImportError as e:
            logging.critical(f"FATAL: Required module cannot be imported: {e}")
            logging.critical("Please ensure dependencies are correctly installed in your virtual environment.")
            sys.exit(1)
        except Exception as e:
            logging.critical(f"An unexpected error occurred while launching WowFactor TUI: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    # Python Version Check (MUST BE FIRST)
    if sys.version_info < (3, 7):
        print("="*80 + "\nFATAL ERROR: INCOMPATIBLE PYTHON VERSION\n" + "="*80)
        print(f"This script requires Python 3.7 or newer. You are using {sys.version.split()[0]}.")
        print("Please update your Python installation from https://www.python.org/downloads/")
        sys.exit(1)
    
    check_and_setup_venv_and_launch()