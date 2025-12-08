# 👾 WOW Factor 👾

![Version](https://img.shields.io/badge/version-1.1.0-ff00ff.svg)

A totally tubular benchmark experience straight from the 80s.

## New in v1.1.0
*   **GameMode Integration**: Automatically requests high-performance mode on Linux systems.
*   **Accurate CPU Frequency Monitoring**: Real-time frequency tracking for precise performance metrics.
*   **Compact UI**: Refined interface for better usability on smaller screens.
*   **Multiprocessing Benchmark**: New benchmark engine utilizes all CPU cores for maximum stress testing.

```
 __      __               ___________              __
/  \    /  \______  _  __ \_   _____/____    _____/  |_  ___________
\   \/\/   /  _ \ \/ \/ /  |    __) \__  \ _/ ___\   __\/  _ \_  __ \
 \        (  <_> )     /   |     \   / __ \\  \___|  | (  <_> )  | \/
  \__/\  / \____/ \/\_/    \___  /  (____  /\___  >__|  \____/|__|
       \/                      \/        \/     \/
```

## What is this?

This project is a benchmark testing tool with a retro 80's theme. It's designed to be a fun, nostalgic way to measure your system's performance.

## System Requirements

To ensure optimal benchmark results, we recommend installing the following system tools:

*   **Linux**: Install `gamemode` to allow the benchmark to request high-performance mode.
    *   Ubuntu/Debian: `sudo apt install gamemode`
    *   Arch Linux: `sudo pacman -S gamemode`
    *   Fedora: `sudo dnf install gamemode`

## Usage

### Installation

First, install the required dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

To start the benchmark tool, run the main script:

```bash
python wowfactor.py
```

### Running Tests

To run the comprehensive test suite:

```bash
pytest tests/
```

## Project Structure

*   `ui/` - Contains the User Interface components (TUI).
*   `core/` - Core logic for benchmarking, power management, and system monitoring.
*   `wowfactor.py` - Main entry point and launcher.
*   `tests/` - Unit and integration tests.
*   `docs/` - Documentation files.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 