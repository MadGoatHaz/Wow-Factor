#!/usr/bin/env python3
"""WowFactor launcher — sets up venv and launches the TUI application."""

import sys
import os
import subprocess
import platform
import logging

VERSION = "1.1.1"

VENV_DIR = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "wowfactor.log")
REQUIRED_PACKAGES = [
    "textual>=0.60.0",
    "psutil>=5.9.0",
    "py-cpuinfo>=9.0.0",
    "textual-plotext>=0.6.0",
    "plotext>=5.0.0",
]


def _setup_launcher_logging() -> None:
    """Simple logging for the venv launcher (pre-venv)."""
    os.makedirs(LOG_DIR, exist_ok=True)
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        handler.close()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode="a"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def check_and_setup_venv_and_launch() -> None:
    """Ensure a virtual environment exists and launch the TUI inside it."""
    _setup_launcher_logging()

    # Ensure requirements.txt is up-to-date for setup
    with open(REQUIREMENTS_FILE, "w") as f:
        for pkg in REQUIRED_PACKAGES:
            f.write(f"{pkg}\n")

    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), VENV_DIR)
    venv_python_executable = os.path.join(venv_path, "Scripts", "python.exe") if platform.system() == "Windows" else os.path.join(venv_path, "bin", "python")

    # Check if running within a virtual environment
    if sys.prefix == sys.base_prefix:
        logging.info("Not running in a virtual environment. Starting setup...")

        if not os.path.exists(venv_path):
            logging.info("Creating virtual environment at %s ...", venv_path)
            try:
                subprocess.check_call([sys.executable, "-m", "venv", venv_path])
                logging.info("Virtual environment created successfully.")
            except Exception as e:
                logging.critical("Fatal: Error creating virtual environment: %s", e)
                sys.exit(1)
        else:
            logging.info("Virtual environment already exists at %s.", venv_path)

        logging.info("Installing/Updating dependencies from %s ...", REQUIREMENTS_FILE)
        try:
            subprocess.check_call([venv_python_executable, "-m", "pip", "install", "--upgrade", "-r", REQUIREMENTS_FILE])
            logging.info("Dependencies installed successfully.")
        except Exception as e:
            logging.critical("Fatal: Dependency installation failed: %s", e)
            sys.exit(1)

        logging.info("Setup complete. Launching application inside the virtual environment...")
        print("\n" + "=" * 80 + "\nSETUP COMPLETE. LAUNCHING APPLICATION...\n" + "=" * 80)

        # Re-launch THIS script inside the virtual environment
        try:
            os.execlp(venv_python_executable, venv_python_executable, os.path.abspath(__file__), *sys.argv[1:])
        except Exception as e:
            logging.critical("Fatal: Error re-launching in virtual environment: %s", e)
            sys.exit(1)
    else:
        # Running inside the virtual environment — launch the TUI
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        # Initialise structured logging BEFORE importing core modules
        from core.logging_config import setup_logging as init_logging
        init_logging(level="INFO", log_file=LOG_FILE)

        logging.info("Running in a virtual environment. Launching WowFactor TUI ...")

        # Check for system dependencies (e.g. GameMode)
        try:
            from core.system_deps import check_gamemode
            check_gamemode()
        except ImportError:
            logging.warning("Could not import system dependency checker.")

        try:
            import textual
            logging.info("Textual %s loaded.", textual.__version__)

            from ui.app import WowFactorTUI

            app = WowFactorTUI()
            app.run()

        except ImportError as e:
            logging.critical("FATAL: Required module cannot be imported: %s", e)
            sys.exit(1)
        except Exception as e:
            logging.critical("Unexpected error launching WowFactor TUI", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    # Python Version Check (MUST BE FIRST)
    if sys.version_info < (3, 12):
        print("=" * 80 + "\nFATAL ERROR: INCOMPATIBLE PYTHON VERSION\n" + "=" * 80)
        print(f"This script requires Python 3.12 or newer. You are using {sys.version.split()[0]}.")
        print("Please update your Python installation from https://www.python.org/downloads/")
        sys.exit(1)

    check_and_setup_venv_and_launch()