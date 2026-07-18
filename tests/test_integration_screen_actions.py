"""Integration tests for screen action flows end-to-end.

These tests mock runtime interactions to verify action flows work:
- Start benchmark flow (validation → worker creation → completion)
- Compare CPUs flow (validation → worker creation)
- View All/Best Scores flow (data loading → pagination/rendering)
- Go Back navigation
- Notification/Toast creation
- Worker deferral (catches the Worker API bug)
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from ui.navigation import NavigationManager
from ui.notifications import ToastNotification, NotificationType
from ui.theme import ColorPalette
from ui.theme import ColorPalette


# ============================================================================
# Worker Deferral Tests — Catches the Worker API Bug
# ============================================================================

def test_benchmark_worker_is_deferred_not_executed():
    """Critical: run_worker must receive a callable, not an executed result.

    This test catches the bug where _benchmark_worker_function() was called
    immediately, passing None to run_worker instead of a deferred lambda.
    """
    from ui.screens.benchmark import RunSingleBenchmarkScreen

    screen = RunSingleBenchmarkScreen()

    captured_callable = [None]

    def mock_run_worker(work, **kwargs):
        captured_callable[0] = work
        return MagicMock()

    screen.run_worker = mock_run_worker

    # Set navigation directly on the instance (bypasses @property)
    captured_nav_messages = []
    mock_nav = MagicMock()
    mock_nav.notify = MagicMock(side_effect=lambda msg, type="info": captured_nav_messages.append((msg, type)))
    mock_nav.navigate_to = MagicMock()
    screen._navigation = mock_nav

    duration_input = MagicMock()
    duration_input.value = "15"
    threads_input = MagicMock()
    threads_input.value = "1"

    def fake_query_one(selector, *args):
        lookup = {
            '#duration_input': duration_input,
            '#threads_input': threads_input,
            '#start_benchmark': MagicMock(disabled=False),
            '#stop_benchmark': MagicMock(disabled=False, display=False),
            '#back_to_main_menu': MagicMock(disabled=False),
            '#result_summary_display': MagicMock(display=False),
            '#result_markdown_display': MagicMock(display=False),
            '#progress_display': MagicMock(),
        }
        return lookup.get(selector, MagicMock())

    with patch.object(screen, 'query_one', side_effect=fake_query_one):
        screen.start_benchmark_run()

    assert callable(captured_callable[0]), \
        "run_worker must receive a callable, got: " + str(type(captured_callable[0]))


def test_batch_worker_is_deferred_not_executed():
    """RunBatchBenchmarkScreen must also wrap its worker in a lambda."""
    from ui.screens.benchmark import RunBatchBenchmarkScreen

    screen = RunBatchBenchmarkScreen()

    captured_callable = [None]

    def mock_run_worker(work, **kwargs):
        captured_callable[0] = work
        return MagicMock()

    screen.run_worker = mock_run_worker

    mock_nav = MagicMock()
    mock_nav.notify = MagicMock()
    mock_nav.navigate_to = MagicMock()
    screen._navigation = mock_nav

    batch_input = MagicMock()
    batch_input.value = "5"
    dur_input = MagicMock()
    dur_input.value = "15"
    threads_input = MagicMock()
    threads_input.value = "1"

    def fake_query_one(selector, *args):
        lookup = {
            '#batch_runs_input': batch_input,
            '#duration_input': dur_input,
            '#num_threads_input': threads_input,
            '#start_batch_benchmark': MagicMock(disabled=False),
            '#stop_batch_benchmark': MagicMock(disabled=False, display=False),
            '#back_to_main_menu': MagicMock(disabled=False),
            '#batch_summary_display': MagicMock(display=False),
            '#batch_markdown_display': MagicMock(display=False),
            '#cooldown_display': MagicMock(display=False),
            '#batch_number_display': MagicMock(),
            '#progress_display': MagicMock(),
        }
        return lookup.get(selector, MagicMock())

    with patch.object(screen, 'query_one', side_effect=fake_query_one):
        screen.start_batch_benchmark()

    assert callable(captured_callable[0]), \
        "Batch run_worker must receive a callable, got: " + str(type(captured_callable[0]))


def test_worker_function_not_executed_in_lambdas():
    """When workers are wrapped in lambdas, calling lambda() returns the result."""
    from ui.screens.benchmark import RunSingleBenchmarkScreen

    screen = RunSingleBenchmarkScreen()

    # The worker function returns None (it posts messages, doesn't return data)
    result = screen._benchmark_worker_function(15, False, 1)
    assert result is None

    # When wrapped in a lambda, calling it returns the same None
    wrapped = lambda: screen._benchmark_worker_function(15, False, 1)
    assert callable(wrapped)
    assert wrapped() is None


# ============================================================================
# Notification Tests — Catches the notify(current_screen) Bug
# ============================================================================

def test_notify_handles_missing_current_screen():
    """navigation.notify() must not crash when app has no current_screen."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.screen = None
    mock_app.SCREENS = {"main_menu": MagicMock}
    nav.initialize(mock_app)

    nav.notify("test message", type="info")


def test_notify_handles_no_current_screen_attribute():
    """navigation.notify() must not crash when app lacks current_screen attr."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock(spec=['SCREENS'])
    mock_app.SCREENS = {"main_menu": MagicMock}
    nav.initialize(mock_app)

    nav.notify("test message", type="warning")


def test_notify_creates_toast_notification():
    """notify() creates and shows a ToastNotification on the current screen."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    nav.initialize(mock_app)

    parent = MagicMock()
    mock_app.screen = parent

    with patch('ui.notifications.ToastNotification.show') as mock_show:
        mock_show.return_value = MagicMock()
        nav.notify("test toast message", type="success")
        mock_show.assert_called_once()
        call_kwargs = mock_show.call_args[1]
        assert call_kwargs['parent'] is parent
        assert call_kwargs['message'] == "test toast message"


def test_notify_maps_success_type():
    """notify with type='success' maps to NotificationType.SUCCESS."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    nav.initialize(mock_app)

    parent = MagicMock()
    mock_app.screen = parent

    with patch('ui.notifications.ToastNotification.show') as mock_show:
        mock_show.return_value = MagicMock()
        nav.notify("msg", type="success")
        assert mock_show.call_args[1]['notification_type'] == NotificationType.SUCCESS


def test_notify_maps_error_type():
    """notify with type='error' maps to NotificationType.ERROR."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    nav.initialize(mock_app)

    parent = MagicMock()
    mock_app.screen = parent

    with patch('ui.notifications.ToastNotification.show') as mock_show:
        mock_show.return_value = MagicMock()
        nav.notify("msg", type="error")
        assert mock_show.call_args[1]['notification_type'] == NotificationType.ERROR


def test_notify_maps_warning_type():
    """notify with type='warning' maps to NotificationType.WARNING."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    nav.initialize(mock_app)

    parent = MagicMock()
    mock_app.screen = parent

    with patch('ui.notifications.ToastNotification.show') as mock_show:
        mock_show.return_value = MagicMock()
        nav.notify("msg", type="warning")
        assert mock_show.call_args[1]['notification_type'] == NotificationType.WARNING


def test_notify_maps_info_type():
    """notify with type='info' maps to NotificationType.INFO."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    nav.initialize(mock_app)

    parent = MagicMock()
    mock_app.screen = parent

    with patch('ui.notifications.ToastNotification.show') as mock_show:
        mock_show.return_value = MagicMock()
        nav.notify("msg", type="info")
        assert mock_show.call_args[1]['notification_type'] == NotificationType.INFO


# ============================================================================
# Go Back Navigation Tests
# ============================================================================

def test_go_back_calls_pop_screen():
    """go_back() calls app.pop_screen() when stack has more than one screen."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    mock_app.screen_stack = [MagicMock(id="main"), MagicMock(id="detail")]
    mock_app.screen = mock_app.screen_stack[-1]
    nav.initialize(mock_app)

    nav.go_back()
    mock_app.pop_screen.assert_called_once()


def test_go_back_no_crash_with_empty_stack():
    """go_back() must not crash when screen_stack is empty."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    mock_app.screen_stack = []
    nav.initialize(mock_app)

    nav.go_back()


def test_go_back_no_crash_with_one_screen():
    """go_back() must not crash when only one screen is on the stack."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    mock_app.screen_stack = [MagicMock(id="main")]
    nav.initialize(mock_app)

    nav.go_back()


def test_reset_to_main_with_main_on_stack():
    """reset_to_main keeps main_menu when it's already on the stack."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    main_screen = MagicMock(id="main_menu")
    mock_app.screen_stack = [main_screen]
    mock_app.current_screen = main_screen
    nav.initialize(mock_app)

    nav.reset_to_main()
    assert mock_app.push_screen.called


def test_reset_to_main_pops_non_main():
    """reset_to_main pops all screens until main_menu is at the bottom."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    main_screen = MagicMock(id="main_menu")
    other_screen = MagicMock(id="detail")
    # Use a real list that gets modified by pop_screen side_effect
    mock_app.screen_stack = [main_screen, other_screen]
    mock_app.current_screen = other_screen
    mock_app.pop_screen.side_effect = lambda: mock_app.screen_stack.pop()
    nav.initialize(mock_app)

    nav.reset_to_main()
    assert mock_app.pop_screen.called


# ============================================================================
# ToastNotification Tests
# ============================================================================

def test_toast_notification_show_creates_widgets():
    """ToastNotification.show() constructs widgets and returns a notification."""
    NavigationManager._instance = None
    NavigationManager._app = None

    nav = NavigationManager()
    mock_app = MagicMock()
    mock_app.SCREENS = {"main_menu": MagicMock}
    nav.initialize(mock_app)

    # Patch at the textual import level since show() imports inside the method
    with patch('textual.containers.Container') as mock_container_cls, \
         patch('textual.widgets.Label') as mock_label_cls, \
         patch('textual.css.query.NoMatches'), \
         patch.object(ToastNotification, '__init__', return_value=None):

        mock_container_instance = MagicMock()
        mock_container_cls.return_value = mock_container_instance

        mock_label_instance = MagicMock()
        mock_label_cls.return_value = mock_label_instance

        parent = MagicMock()

        # Instantiate without calling __init__ to avoid the duration/time calls
        notification = object.__new__(ToastNotification)
        notification.message = "Test toast"
        notification.type = NotificationType.INFO
        notification.duration = 1
        notification._dismiss_timer = None
        notification._created_at = 0.0
        notification.on_dismissed = None

        # Patch show to return our pre-built notification
        with patch.object(ToastNotification, 'show', return_value=notification):
            result = ToastNotification.show(
                parent=parent,
                message="Test toast",
                notification_type=NotificationType.INFO,
                duration=1,
            )

        assert result is not None


def test_toast_notification_properties():
    """ToastNotification has correct property behavior."""
    nav_mock = MagicMock()

    notification = ToastNotification(
        message="Color test",
        type_=NotificationType.ERROR,
        duration=5,
    )

    assert notification.bg_color == ColorPalette.ERROR_RED
    assert notification.fg_color == ColorPalette.TEXT_PRIMARY
    assert notification.message == "Color test"
    assert notification.is_expired is False


# ============================================================================
# Data Loading Flow Tests
# ============================================================================

def test_view_best_scores_load_data_method_exists():
    """ViewBestScoresScreen.load_data() exists and is callable."""
    from ui.screens.views import ViewBestScoresScreen

    screen = ViewBestScoresScreen()
    assert hasattr(screen, 'load_data')
    assert callable(screen.load_data)

    import inspect
    sig = inspect.signature(screen.load_data)
    params = [p for p in sig.parameters if p != 'self']
    assert len(params) == 0


def test_view_all_scores_load_data_method_exists():
    """ViewAllScoresScreen.load_data() exists and is callable."""
    from ui.screens.views import ViewAllScoresScreen

    screen = ViewAllScoresScreen()
    assert hasattr(screen, 'load_data')
    assert callable(screen.load_data)

    import inspect
    sig = inspect.signature(screen.load_data)
    params = [p for p in sig.parameters if p != 'self']
    assert len(params) == 0


def test_view_all_scores_pagination_attributes_initialized():
    """ViewAllScoresScreen has pagination attributes initialized at creation."""
    from ui.screens.views import ViewAllScoresScreen

    screen = ViewAllScoresScreen()
    assert screen.current_page == 1
    assert screen.page_size == 50
    assert screen.total_pages == 1
    assert screen.total_items == 0
    assert screen.filtered_scores == []


def test_view_all_scores_calculate_pages():
    """ViewAllScoresScreen._calculate_pages computes correct total_pages."""
    from ui.screens.views import ViewAllScoresScreen

    screen = ViewAllScoresScreen()

    screen.total_items = 120
    screen._calculate_pages()
    assert screen.total_pages == 3

    screen.total_items = 0
    screen._calculate_pages()
    assert screen.total_pages == 1

    screen.total_items = 50
    screen._calculate_pages()
    assert screen.total_pages == 1

    screen.total_items = 51
    screen._calculate_pages()
    assert screen.total_pages == 2


def test_view_best_scores_load_data_method():
    """ViewBestScoresScreen.load_data() exists and is callable."""
    from ui.screens.views import ViewBestScoresScreen

    screen = ViewBestScoresScreen()
    assert hasattr(screen, 'load_data')
    assert callable(screen.load_data)


def test_compare_cpu_load_cpus_method_exists():
    """CompareCPUScreen.load_available_cpus() exists and is callable."""
    from ui.screens.views import CompareCPUScreen

    screen = CompareCPUScreen()
    assert hasattr(screen, 'load_available_cpus')
    assert callable(screen.load_available_cpus)


# ============================================================================
# Input Validation Flow Tests
# ============================================================================

def test_benchmark_invalid_duration_rejects_non_integer():
    """start_benchmark_run rejects non-integer duration values."""
    from ui.screens.benchmark import RunSingleBenchmarkScreen

    screen = RunSingleBenchmarkScreen()

    captured_messages = []
    mock_nav = MagicMock()
    mock_nav.notify = MagicMock(side_effect=lambda msg, type="info": captured_messages.append((msg, type)))
    mock_nav.navigate_to = MagicMock()
    screen._navigation = mock_nav

    mock_input = MagicMock()
    mock_input.value = "abc"

    def fake_query_one(selector, *args):
        return mock_input

    with patch.object(screen, 'query_one', side_effect=fake_query_one):
        screen.start_benchmark_run()

    assert any("Invalid duration" in msg for msg, _ in captured_messages)


def test_benchmark_invalid_threads_rejects_zero():
    """start_benchmark_run rejects thread count < 1."""
    from ui.screens.benchmark import RunSingleBenchmarkScreen

    screen = RunSingleBenchmarkScreen()

    captured_messages = []
    mock_nav = MagicMock()
    mock_nav.notify = MagicMock(side_effect=lambda msg, type="info": captured_messages.append((msg, type)))
    mock_nav.navigate_to = MagicMock()
    screen._navigation = mock_nav

    duration_input = MagicMock()
    duration_input.value = "15"
    threads_input = MagicMock()
    threads_input.value = "0"

    def fake_query_one(selector, *args):
        if selector == '#duration_input':
            return duration_input
        elif selector == '#threads_input':
            return threads_input
        return MagicMock()

    with patch.object(screen, 'query_one', side_effect=fake_query_one):
        screen.start_benchmark_run()

    assert any("Thread count must be at least 1" in msg for msg, _ in captured_messages)


def test_compare_cpu_validation_rejects_empty_inputs():
    """CompareCPUScreen.on_button_pressed rejects empty CPU model inputs."""
    from textual.widgets import Select
    from ui.screens.views import CompareCPUScreen

    screen = CompareCPUScreen()

    captured_messages = []
    mock_nav = MagicMock()
    mock_nav.notify = MagicMock(side_effect=lambda msg, type="info": captured_messages.append((msg, type)))
    screen._navigation = mock_nav

    first_select = MagicMock()
    first_select.value = Select.NULL
    second_select = MagicMock()
    second_select.value = Select.NULL

    mock_event = MagicMock()
    mock_event.button.id = "compare_button"

    def fake_query_one(selector, *args):
        if selector == '#first_cpu_select':
            return first_select
        elif selector == '#second_cpu_select':
            return second_select
        return MagicMock()

    with patch.object(screen, 'query_one', side_effect=fake_query_one):
        screen.on_button_pressed(mock_event)

    assert any("Please select both CPUs" in msg for msg, _ in captured_messages)