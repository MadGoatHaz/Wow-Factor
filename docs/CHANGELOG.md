# Changelog

All notable changes to the WOW Factor TUI project will be documented in this file.

## [1.1.0] - 2025-12-08

### Added
- **GameMode Integration**: Added support for Feral Interactive's GameMode on Linux to request high-performance mode during benchmarks.
- **Accurate Frequency Monitoring**: Implemented real-time CPU frequency tracking using `psutil` (and `/proc/cpuinfo` on Linux) for precise performance metrics.
- **Benchmark Engine V2**:
    - **Multiprocessing**: Replaced threading with multiprocessing to bypass the GIL and fully utilize all CPU cores.
    - **Math-Heavy Workload**: Switched to a complex floating-point calculation model (sin, cos, sqrt) for more realistic stress testing.
    - **Warmup Phase**: Added a 2-second warmup period before measurement to allow CPU frequency to stabilize at peak levels.
- **Compact UI**: Refined the user interface to be more compact and usable on smaller screens (e.g., 80x24 terminals).

### Changed
- **Project Structure**: Refactored the codebase into a modular structure:
    - `core/`: Contains core logic (benchmarking, power management, system dependencies).
    - `ui/`: Contains UI components and screens.
    - `wowfactor.py`: Simplified entry point.
- **Documentation**: Updated `README.md` and `DOCUMENTATION.md` to reflect the new architecture and features.

### Fixed
- **Pagination**: Removed complex and buggy pagination logic in favor of a simpler, more robust approach.
- **Charts**: Removed incomplete chart implementation to focus on core stability.