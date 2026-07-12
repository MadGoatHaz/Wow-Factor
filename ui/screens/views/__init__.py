# ui/screens/views/__init__.py: Views package re-exports
#
# Provides backward-compatible imports for all screen classes
# that were previously available from ui.screens.views.

from .rendering import ViewBestScoresScreen
from .charts import CompareCPUScreen
from .navigation import ViewAllScoresScreen

__all__ = [
    'ViewBestScoresScreen',
    'CompareCPUScreen',
    'ViewAllScoresScreen',
]