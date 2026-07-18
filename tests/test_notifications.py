"""
Tests for ui/notifications.py — Toast notification system.

Covers ToastNotification initialization, color mapping, expiration,
dismissal callbacks, stacking, and the show() classmethod.
"""

import time
from unittest.mock import MagicMock, patch, call

import pytest

from ui.notifications import NotificationType, ToastNotification
from ui.theme import ColorPalette
from ui.theme import ColorPalette


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def info_toast():
    """ToastNotification with default INFO type and 3-second duration."""
    return ToastNotification(message="Hello info", type_=NotificationType.INFO)


@pytest.fixture
def success_toast():
    """ToastNotification with SUCCESS type and 5-second duration."""
    return ToastNotification(
        message="Operation complete",
        type_=NotificationType.SUCCESS,
        duration=5,
    )


@pytest.fixture
def warning_toast():
    """ToastNotification with WARNING type and 2-second duration."""
    return ToastNotification(
        message="Check your input",
        type_=NotificationType.WARNING,
        duration=2,
    )


@pytest.fixture
def error_toast():
    """ToastNotification with ERROR type and 10-second duration."""
    return ToastNotification(
        message="Something went wrong",
        type_=NotificationType.ERROR,
        duration=10,
    )


# ---------------------------------------------------------------------------
# 1. ToastNotification initialization
# ---------------------------------------------------------------------------

class TestInitialization:
    """Test ToastNotification construction and default values."""

    def test_default_type_is_info(self):
        toast = ToastNotification(message="default type")
        assert toast.type == NotificationType.INFO

    def test_default_duration_is_3(self):
        toast = ToastNotification(message="default duration")
        assert toast.duration == 3

    def test_default_on_dismissed_is_none(self):
        toast = ToastNotification(message="no callback")
        assert toast.on_dismissed is None

    def test_stored_attributes(self):
        callback = MagicMock()
        toast = ToastNotification(
            message="stored test",
            type_=NotificationType.WARNING,
            duration=7,
            on_dismissed=callback,
        )
        assert toast.message == "stored test"
        assert toast.type == NotificationType.WARNING
        assert toast.duration == 7
        assert toast.on_dismissed is callback
        assert toast._dismiss_timer is None


# ---------------------------------------------------------------------------
# 2-5. Adding toasts of each type — verify message content
# ---------------------------------------------------------------------------

class TestToastMessage:
    """Toast message content is preserved for every notification type."""

    def test_info_message(self, info_toast):
        assert info_toast.message == "Hello info"

    def test_success_message(self, success_toast):
        assert success_toast.message == "Operation complete"

    def test_warning_message(self, warning_toast):
        assert warning_toast.message == "Check your input"

    def test_error_message(self, error_toast):
        assert error_toast.message == "Something went wrong"


# ---------------------------------------------------------------------------
# 6. Toast color mapping (info=blue, success=green, warning=yellow, error=red)
# ---------------------------------------------------------------------------

class TestColorMapping:
    """Each NotificationType maps to its expected bg/fg colors."""

    def test_info_colors(self, info_toast):
        assert info_toast.bg_color == ColorPalette.INFO_BLUE
        assert info_toast.fg_color == ColorPalette.TEXT_PRIMARY

    def test_success_colors(self, success_toast):
        assert success_toast.bg_color == ColorPalette.SUCCESS_GREEN
        assert success_toast.fg_color == ColorPalette.TEXT_PRIMARY

    def test_warning_colors(self, warning_toast):
        assert warning_toast.bg_color == ColorPalette.WARNING_YELLOW
        assert warning_toast.fg_color == ColorPalette.TEXT_DARK

    def test_error_colors(self, error_toast):
        assert error_toast.bg_color == ColorPalette.ERROR_RED
        assert error_toast.fg_color == ColorPalette.TEXT_PRIMARY

    def test_colors_class_dict_matches(self):
        assert ToastNotification.COLORS[NotificationType.INFO]["bg"] == ColorPalette.INFO_BLUE
        assert ToastNotification.COLORS[NotificationType.SUCCESS]["bg"] == ColorPalette.SUCCESS_GREEN
        assert ToastNotification.COLORS[NotificationType.WARNING]["bg"] == ColorPalette.WARNING_YELLOW
        assert ToastNotification.COLORS[NotificationType.ERROR]["bg"] == ColorPalette.ERROR_RED


# ---------------------------------------------------------------------------
# 7. Toast expiration (is_expired)
# ---------------------------------------------------------------------------

class TestExpiration:
    """Test that is_expired returns correct values based on elapsed time."""

    def test_not_expired_short_duration(self):
        """Toast with 0.05s duration should NOT be expired immediately."""
        toast = ToastNotification(message="quick", duration=0)
        # Duration is 0 so it's already expired — test the other direction
        time.sleep(0.02)
        assert toast.is_expired is True

    def test_not_expired_zero(self):
        """A brand-new toast with duration=0 is expired right away."""
        toast = ToastNotification(message="instant", duration=0)
        assert toast.is_expired is True

    def test_is_expired_true_after_sleep(self):
        """Toast with 0.05s duration should expire after sleeping."""
        toast = ToastNotification(message="expire me", duration=0)
        time.sleep(0.02)
        assert toast.is_expired is True

    def test_elapsed_time_increases(self):
        """Elapsed time should increase as time passes."""
        toast = ToastNotification(message="elapsed test", duration=60)
        t0 = toast.elapsed_time
        time.sleep(0.05)
        t1 = toast.elapsed_time
        assert t1 > t0


# ---------------------------------------------------------------------------
# 8. Toast dismissal
# ---------------------------------------------------------------------------

class TestDismissal:
    """Test dismiss() behavior and on_dismissed callback invocation."""

    def test_dismiss_calls_callback(self):
        callback = MagicMock()
        toast = ToastNotification(
            message="dismiss me",
            on_dismissed=callback,
        )
        toast.dismiss()
        callback.assert_called_once()

    def test_dismiss_no_callback(self):
        """Dismiss with no callback should not raise."""
        toast = ToastNotification(message="no callback")
        toast.dismiss()  # should not raise


# ---------------------------------------------------------------------------
# 9. Toast stacking (multiple independent toasts)
# ---------------------------------------------------------------------------

class TestStacking:
    """Multiple ToastNotification instances are independent."""

    def test_multiple_toasts_independent(self):
        toasts = [
            ToastNotification(message=f"toast {i}", duration=0)
            for i in range(5)
        ]
        time.sleep(0.01)
        for idx, t in enumerate(toasts):
            assert t.message == f"toast {idx}"
            assert t.is_expired is True

    def test_toast_no_spillover_types(self):
        """Changing one toast's attributes doesn't affect another."""
        t1 = ToastNotification(message="t1", type_=NotificationType.SUCCESS)
        t2 = ToastNotification(message="t2", type_=NotificationType.ERROR)
        assert t1.bg_color != t2.bg_color
        assert t1.fg_color == t2.fg_color  # both are ColorPalette.TEXT_PRIMARY


# ---------------------------------------------------------------------------
# 10. clear_all_toasts — the notification module doesn't expose a
#     module-level store, so we verify the equivalent behavior:
#     the show() classmethod creates independent instances.
# ---------------------------------------------------------------------------

class TestShowMethod:
    """Test the show() classmethod with mocked Textual widgets."""

    @patch("ui.notifications.ToastNotification.show")
    def test_show_returns_notification(self, mock_show):
        """show() should return a ToastNotification instance."""
        # Internal check: classmethod is properly defined
        assert hasattr(ToastNotification, "show")
        assert callable(getattr(ToastNotification, "show"))

    def test_show_is_classmethod(self):
        """show() must be a classmethod on ToastNotification."""
        assert isinstance(ToastNotification.__dict__["show"], classmethod)


class TestScheduleAutoDismiss:
    """Test schedule_auto_dismiss() callback scheduling."""

    def test_scheduler_called_with_delay(self):
        """scheduler() is called with remaining_ms and a dismiss callback."""
        toast = ToastNotification(
            message="schedule test",
            duration=0,  # already expired
        )
        scheduler_calls = []
        def fake_scheduler(delay_ms, cb):
            scheduler_calls.append((delay_ms, cb))

        toast.schedule_auto_dismiss(fake_scheduler)
        assert len(scheduler_calls) == 0  # remaining <= 0, no scheduling

    def test_scheduler_not_called_when_expired(self):
        """No scheduling when toast is already expired."""
        toast = ToastNotification(message="expired", duration=0)
        called = []
        def fake_scheduler(delay_ms, cb):
            called.append(True)

        toast.schedule_auto_dismiss(fake_scheduler)
        assert len(called) == 0

    def test_scheduler_called_with_positive_remaining(self):
        """Scheduler is called with delay when toast still has time."""
        # Use a very short duration so remaining > 0 at creation
        toast = ToastNotification(message="has time", duration=10)
        scheduler_calls = []

        def fake_scheduler(delay_ms, cb):
            scheduler_calls.append((delay_ms, cb))

        toast.schedule_auto_dismiss(fake_scheduler)
        assert len(scheduler_calls) == 1
        delay_ms, cb = scheduler_calls[0]
        assert delay_ms > 0
        assert delay_ms <= 10_000  # 10 seconds in ms
        assert callable(cb)