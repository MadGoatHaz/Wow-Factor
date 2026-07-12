"""Tests for ui/navigation.py — NavigationManager singleton service."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from ui.navigation import NavigationManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _fresh_manager_and_app():
    """Return a clean NavigationManager and MockApp, resetting singleton state."""
    NavigationManager._instance = None
    NavigationManager._app = None
    nav = NavigationManager()

    class MockApp:
        SCREENS = {}

        def __init__(self):
            self.screen_stack = []
            self.current_screen = None

        def push_screen(self, screen):
            self.screen_stack.append(screen)
            self.current_screen = screen

        def pop_screen(self):
            if self.screen_stack:
                return self.screen_stack.pop()

    app = MockApp()
    nav.initialize(app)
    return nav, app


@pytest.fixture
def fresh_nav():
    """Yield a fresh NavigationManager with a MockApp, then reset singleton."""
    nav, app = _fresh_manager_and_app()
    yield nav, app
    NavigationManager._instance = None
    NavigationManager._app = None


@pytest.fixture
def nav_with_screen_registry():
    """NavigationManager with a toy screen registry containing a 'dashboard' screen."""

    class DashboardScreen:
        def __init__(self, label=None):
            self.label = label
            self.id = "dashboard"

    nav, app = _fresh_manager_and_app()
    app.SCREENS = {"dashboard": DashboardScreen}
    yield nav, app, DashboardScreen
    NavigationManager._instance = None
    NavigationManager._app = None


@pytest.fixture
def nav_with_multi_screen_registry():
    """NavigationManager with multiple screen aliases."""

    class HomeScreen:
        def __init__(self):
            self.id = "home"

    class SettingsScreen:
        def __init__(self, tab=None):
            self.tab = tab
            self.id = "settings"

    class ErrorScreen:
        def __init__(self, code=None):
            self.code = code
            self.id = "error"

    nav, app = _fresh_manager_and_app()
    app.SCREENS = {
        "home": HomeScreen,
        "settings": SettingsScreen,
        "error": ErrorScreen,
    }
    yield nav, app, {"home": HomeScreen, "settings": SettingsScreen, "error": ErrorScreen}
    NavigationManager._instance = None
    NavigationManager._app = None


# ---------------------------------------------------------------------------
# 1. Singleton pattern
# ---------------------------------------------------------------------------

def test_singleton_returns_same_instance(fresh_nav):
    """Two calls to NavigationManager() return the same instance."""
    nav1, _ = fresh_nav
    nav2 = NavigationManager()
    assert nav1 is nav2


def test_singleton_reset_produces_new_instance():
    """After resetting the singleton, the next call creates a new instance."""
    NavigationManager._instance = None
    NavigationManager._app = None
    nav1 = NavigationManager()
    NavigationManager._instance = None
    NavigationManager._app = None
    nav2 = NavigationManager()
    assert nav1 is not nav2


# ---------------------------------------------------------------------------
# 2. Initialization
# ---------------------------------------------------------------------------

def test_initialize_sets_app_reference(fresh_nav):
    """initialize() stores the app reference."""
    nav, app = fresh_nav
    assert nav.app is app


def test_app_property_raises_before_init():
    """Accessing app before initialize() raises RuntimeError."""
    NavigationManager._instance = None
    NavigationManager._app = None
    nav = NavigationManager()
    with pytest.raises(RuntimeError, match="not initialized"):
        _ = nav.app


# ---------------------------------------------------------------------------
# 3. Navigate to a new screen (push to history)
# ---------------------------------------------------------------------------

def test_navigate_to_pushes_screen(fresh_nav):
    """navigate_to() with a valid screen pushes it onto the app's screen stack."""

    class DummyScreen:
        pass

    nav, app = fresh_nav
    app.SCREENS = {"dummy": DummyScreen}
    nav.navigate_to("dummy")

    assert len(app.screen_stack) == 1
    assert isinstance(app.screen_stack[0], DummyScreen)
    assert app.current_screen is app.screen_stack[0]


def test_navigate_to_passes_kwargs_to_screen():
    """navigate_to() forwards keyword arguments to the screen constructor."""

    class GreetScreen:
        def __init__(self, name=None):
            self.name = name

    nav, app = _fresh_manager_and_app()
    app.SCREENS = {"greet": GreetScreen}
    nav.navigate_to("greet", name="Alice")

    screen = app.screen_stack[0]
    assert isinstance(screen, GreetScreen)
    assert screen.name == "Alice"


# ---------------------------------------------------------------------------
# 4. Navigate to invalid screen (error handling)
# ---------------------------------------------------------------------------

def test_navigate_to_invalid_screen_raises_value_error(fresh_nav):
    """navigate_to() with an unknown screen name raises ValueError."""
    nav, app = fresh_nav
    app.SCREENS = {"only_one": Mock()}
    with pytest.raises(ValueError, match="Unknown screen name"):
        nav.navigate_to("nonexistent")


def test_navigate_to_invalid_screen_error_message_lists_available():
    """ValueError message includes the list of available screens."""
    nav, app = _fresh_manager_and_app()
    app.SCREENS = {"alpha": Mock(), "beta": Mock()}
    with pytest.raises(ValueError) as exc_info:
        nav.navigate_to("gamma")
    assert "alpha" in str(exc_info.value)
    assert "beta" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 5. Navigate back (go_back)
# ---------------------------------------------------------------------------

def test_go_back_pops_screen(fresh_nav):
    """go_back() pops the top screen when stack has more than one."""
    nav, app = fresh_nav

    class S1:
        pass

    class S2:
        pass

    app.SCREENS = {"s1": S1, "s2": S2}
    nav.navigate_to("s1")
    nav.navigate_to("s2")
    assert len(app.screen_stack) == 2

    nav.go_back()
    assert len(app.screen_stack) == 1
    assert isinstance(app.screen_stack[0], S1)


def test_go_back_noop_when_single_screen(fresh_nav):
    """go_back() does nothing when the stack has only one screen."""
    nav, app = fresh_nav

    class S1:
        pass

    app.SCREENS = {"s1": S1}
    nav.navigate_to("s1")
    original_len = len(app.screen_stack)
    nav.go_back()
    assert len(app.screen_stack) == original_len


def test_go_back_noop_when_empty_stack(fresh_nav):
    """go_back() does nothing when the stack is empty."""
    nav, app = fresh_nav
    app.screen_stack = []
    nav.go_back()
    assert len(app.screen_stack) == 0


# ---------------------------------------------------------------------------
# 6. Multiple sequential navigations
# ---------------------------------------------------------------------------

def test_multiple_sequential_navigations():
    """Stack grows with each navigate_to call."""
    nav, app = _fresh_manager_and_app()

    class S:
        def __init__(self, idx):
            self.idx = idx

    app.SCREENS = {"s": S}
    nav.navigate_to("s", idx=1)
    nav.navigate_to("s", idx=2)
    nav.navigate_to("s", idx=3)

    assert len(app.screen_stack) == 3
    assert [s.idx for s in app.screen_stack] == [1, 2, 3]


def test_rapid_navigation_changes():
    """Rapid push/pop cycles are handled correctly."""
    nav, app = _fresh_manager_and_app()

    class A:
        pass

    class B:
        pass

    class C:
        pass

    app.SCREENS = {"a": A, "b": B, "c": C}
    nav.navigate_to("a")
    nav.navigate_to("b")
    nav.navigate_to("c")
    nav.go_back()
    nav.navigate_to("b")

    assert len(app.screen_stack) == 3
    assert [type(s).__name__ for s in app.screen_stack] == ["A", "B", "B"]


# ---------------------------------------------------------------------------
# 7. Navigation state persistence (singleton)
# ---------------------------------------------------------------------------

def test_navigation_state_persists_across_method_calls():
    """State is preserved because NavigationManager is a singleton."""
    nav, app = _fresh_manager_and_app()

    class Dash:
        pass

    app.SCREENS = {"dash": Dash}
    nav.navigate_to("dash")
    stack_after_first = len(app.screen_stack)

    nav.navigate_to("dash")
    stack_after_second = len(app.screen_stack)

    assert stack_after_second == stack_after_first + 1


def test_screen_class_instantiated_per_navigation():
    """Each navigate_to call creates a new screen instance (no reuse)."""
    nav, app = _fresh_manager_and_app()

    instances = []

    class Trackable:
        def __init__(self):
            instances.append(self)

    app.SCREENS = {"track": Trackable}
    nav.navigate_to("track")
    nav.navigate_to("track")

    assert len(instances) == 2
    assert instances[0] is not instances[1]


# ---------------------------------------------------------------------------
# 8. Reset to main (reset_to_main)
# ---------------------------------------------------------------------------

def test_reset_to_main_clears_stack(fresh_nav):
    """reset_to_main() pops all screens until only one remains."""

    class Dummy:
        pass

    nav, app = fresh_nav
    app.SCREENS = {"dummy": Dummy}
    nav.navigate_to("dummy")
    nav.navigate_to("dummy")
    nav.navigate_to("dummy")
    assert len(app.screen_stack) == 3

    nav.reset_to_main()
    assert len(app.screen_stack) == 1


def test_reset_to_main_pushes_main_menu_if_missing():
    """reset_to_main() pushes 'main_menu' when top screen is not main_menu."""

    class Other:
        id = "other"

    nav, app = _fresh_manager_and_app()
    app.SCREENS = {}
    app.current_screen = Other()

    calls = []

    def capture_push(screen):
        calls.append(screen)
        app.screen_stack.append(screen)

    app.push_screen = capture_push
    nav.reset_to_main()

    assert "main_menu" in calls


# ---------------------------------------------------------------------------
# 9. Notify (toast)
# ---------------------------------------------------------------------------

def test_notify_calls_show_success():
    """notify(type='success') dispatches a SUCCESS toast."""
    nav, app = _fresh_manager_and_app()
    app.SCREENS = {}

    mock_screen = Mock()
    mock_screen.id = "test"
    app.current_screen = mock_screen

    with patch("ui.notifications.ToastNotification") as MockToast:
        nav.notify("done", type="success")
        MockToast.show.assert_called_once()
        kwargs = MockToast.show.call_args.kwargs
        assert kwargs["message"] == "done"
        assert kwargs["notification_type"].value == "success"


def test_notify_calls_show_error():
    """notify(type='error') dispatches an ERROR toast."""
    nav, app = _fresh_manager_and_app()
    mock_screen = Mock()
    mock_screen.id = "test"
    app.current_screen = mock_screen

    with patch("ui.notifications.ToastNotification") as MockToast:
        nav.notify("fail", type="error")
        kwargs = MockToast.show.call_args.kwargs
        assert kwargs["notification_type"].value == "error"


def test_notify_calls_show_with_unknown_type_defaults_to_info():
    """notify with an unknown type defaults to INFO."""
    nav, app = _fresh_manager_and_app()
    mock_screen = Mock()
    app.current_screen = mock_screen

    with patch("ui.notifications.ToastNotification") as MockToast:
        nav.notify("huh", type="bogus")
        kwargs = MockToast.show.call_args.kwargs
        assert kwargs["notification_type"].value == "info"


def test_notify_noop_when_no_current_screen():
    """notify does nothing when app.current_screen is None."""
    nav, app = _fresh_manager_and_app()
    app.current_screen = None

    with patch("ui.notifications.ToastNotification") as MockToast:
        nav.notify("hello")
        MockToast.show.assert_not_called()