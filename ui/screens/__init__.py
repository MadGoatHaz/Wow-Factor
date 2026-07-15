"""
Screen modules for WowFactor UI.

This package contains extracted screen classes that provide modular
dependency injection via the ScreenWithServices mixin.
"""

from .base_screen import ScreenWithServices, BaseScreen
from .main_menu import MainMenuScreen
from .benchmark import RunSingleBenchmarkScreen, RunBatchBenchmarkScreen
from .views import ViewBestScoresScreen, CompareCPUScreen, ViewAllScoresScreen
from .analytics import AnalyticsScreen, TrendsChartScreen
from .cleanup import ClearInvalidScoresResultScreen
from .overlay import LoadingOverlay
from .confirmation import ClearInvalidScoresConfirmationScreen, ClearInvalidScoresConfirmed

__all__ = [
    'ScreenWithServices',
    'BaseScreen',
    'MainMenuScreen',
    'RunSingleBenchmarkScreen',
    'RunBatchBenchmarkScreen',
    'ViewBestScoresScreen',
    'CompareCPUScreen',
    'ViewAllScoresScreen',
    'AnalyticsScreen',
    'TrendsChartScreen',
    'ClearInvalidScoresResultScreen',
    'LoadingOverlay',
    'ClearInvalidScoresConfirmationScreen',
    'ClearInvalidScoresConfirmed',
]
