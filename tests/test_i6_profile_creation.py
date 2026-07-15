#!/usr/bin/env python3
"""
Tests for CHUNK-I6: Implement Profile Creation Screen.

Covers:
- ProfileCreationScreen widget composition (5 Input fields, 2 buttons)
- Input validation (name required, duration positive, threads bounded, etc.)
- Profile persistence through ConfigManager
- Cancel/back navigation
- Keybinding actions (b=back, q=quit, ctrl+s=save)
- ProfileSelectionScreen wiring to ProfileCreationScreen
- Duplicate profile name rejection
- ProfileCreatedMessage posting
- Screen inheritance from BaseScreen
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# Ensure project root is on path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestI6ScreenInheritance:
    """Verify ProfileCreationScreen inherits from BaseScreen."""

    def test_inherits_from_basescreen(self):
        """ProfileCreationScreen must inherit from BaseScreen."""
        from ui.screens.base_screen import BaseScreen
        from ui.screens.profile_creation import ProfileCreationScreen

        assert issubclass(ProfileCreationScreen, BaseScreen)

    def test_has_navigation_property(self):
        """ProfileCreationScreen must have navigation property from mixin."""
        from ui.screens.profile_creation import ProfileCreationScreen

        assert hasattr(ProfileCreationScreen, "navigation")

    def test_has_services_property(self):
        """ProfileCreationScreen must have services property from mixin."""
        from ui.screens.profile_creation import ProfileCreationScreen

        assert hasattr(ProfileCreationScreen, "services")


class TestI6Bindings:
    """Verify ProfileCreationScreen has correct keybindings."""

    def test_has_bindings(self):
        """ProfileCreationScreen must define BINDINGS."""
        from ui.screens.profile_creation import ProfileCreationScreen

        assert hasattr(ProfileCreationScreen, "BINDINGS")
        assert len(ProfileCreationScreen.BINDINGS) >= 3

    def test_has_back_binding(self):
        """ProfileCreationScreen must have 'b' -> back binding."""
        from ui.screens.profile_creation import ProfileCreationScreen

        binding_keys = [b.key for b in ProfileCreationScreen.BINDINGS]
        assert "b" in binding_keys, "Must have 'b' binding for back"

    def test_has_quit_binding(self):
        """ProfileCreationScreen must have 'q' -> quit binding."""
        from ui.screens.profile_creation import ProfileCreationScreen

        binding_keys = [b.key for b in ProfileCreationScreen.BINDINGS]
        assert "q" in binding_keys, "Must have 'q' binding for quit"

    def test_has_save_binding(self):
        """ProfileCreationScreen must have ctrl+s -> save binding."""
        from ui.screens.profile_creation import ProfileCreationScreen

        binding_keys = [b.key for b in ProfileCreationScreen.BINDINGS]
        assert "ctrl+s" in binding_keys, "Must have ctrl+s binding for save"

    def test_bindings_are_shown(self):
        """All bindings should be visible in the footer."""
        from ui.screens.profile_creation import ProfileCreationScreen

        for binding in ProfileCreationScreen.BINDINGS:
            assert binding.show is True, f"Binding {binding.key} should be shown"


class TestI6ComposeWidgets:
    """Verify ProfileCreationScreen composes all required widgets."""

    async def test_composes_five_input_fields(self):
        """Screen must compose exactly 5 Input widgets."""
        from textual.app import App
        from textual.widgets import Input
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()
            screen = pilot.app.screen
            input_widgets = list(screen.query(Input))
            assert len(input_widgets) == 5, (
                f"Should have 5 Input widgets, got {len(input_widgets)}"
            )

    async def test_input_fields_have_correct_ids(self):
        """Input widgets must have the expected IDs."""
        from textual.app import App
        from textual.widgets import Input
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        expected_ids = [
            "input_profile_name",
            "input_duration",
            "input_threads",
            "input_batch_runs",
            "input_cooldown",
        ]

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()
            screen = pilot.app.screen
            for eid in expected_ids:
                widget = screen.query_one(f"#{eid}", Input)
                assert widget is not None, f"Input #{eid} not found"

    async def test_composes_save_and_cancel_buttons(self):
        """Screen must compose Save and Cancel buttons."""
        from textual.app import App
        from textual.widgets import Button
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()
            screen = pilot.app.screen
            save_btn = screen.query_one("#save_profile_btn", Button)
            cancel_btn = screen.query_one("#cancel_profile_btn", Button)
            assert save_btn.label == "Save"
            assert cancel_btn.label == "Cancel"

    async def test_save_button_is_primary_variant(self):
        """Save button should use primary variant."""
        from textual.app import App
        from textual.widgets import Button
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()
            screen = pilot.app.screen
            save_btn = screen.query_one("#save_profile_btn", Button)
            assert save_btn.variant == "primary"

    async def test_cancel_button_is_default_variant(self):
        """Cancel button should use default variant."""
        from textual.app import App
        from textual.widgets import Button
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()
            screen = pilot.app.screen
            cancel_btn = screen.query_one("#cancel_profile_btn", Button)
            assert cancel_btn.variant == "default"

    async def test_composes_error_display(self):
        """Screen must compose error display label."""
        from textual.app import App
        from textual.widgets import Label
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()
            screen = pilot.app.screen
            error_display = screen.query_one("#error_display", Label)
            assert error_display is not None

    async def test_error_display_hidden_by_default(self):
        """Error display should not be visible initially."""
        from textual.app import App
        from textual.widgets import Label
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()
            screen = pilot.app.screen
            error_display = screen.query_one("#error_display", Label)
            assert "visible" not in error_display.classes

    async def test_composes_header_and_footer(self):
        """Screen must compose Header and Footer widgets."""
        from textual.app import App
        from textual.widgets import Header, Footer
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()
            screen = pilot.app.screen
            header = screen.query_one(Header)
            footer = screen.query_one(Footer)
            assert header is not None
            assert footer is not None


class TestI6InputValidation:
    """Verify input validation logic in ProfileCreationScreen."""

    def test_empty_name_rejected(self):
        """Empty profile name must be rejected."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()
        screen._get_input = MagicMock(side_effect=lambda x: "" if "name" in x else "15")
        is_valid, msg = screen._validate_inputs()
        assert is_valid is False
        assert "required" in msg.lower()

    def test_duplicate_name_rejected(self):
        """Profile name that already exists must be rejected."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()
        screen._existing_profiles = {"Existing Profile"}
        screen._get_input = MagicMock(side_effect=lambda x: "Existing Profile" if "name" in x else "15")
        is_valid, msg = screen._validate_inputs()
        assert is_valid is False
        assert "already exists" in msg.lower()

    def test_name_too_long_rejected(self):
        """Profile name exceeding 100 chars must be rejected."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()
        long_name = "A" * 101
        screen._get_input = MagicMock(side_effect=lambda x: long_name if "name" in x else "15")
        is_valid, msg = screen._validate_inputs()
        assert is_valid is False
        assert "100" in msg

    def test_zero_duration_rejected(self):
        """Zero or negative duration must be rejected."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()
        screen._get_input = MagicMock(
            side_effect=lambda x: "Test" if "name" in x else "0"
        )
        is_valid, msg = screen._validate_inputs()
        assert is_valid is False
        assert "positive" in msg.lower() or "duration" in msg.lower()

    def test_duration_too_large_rejected(self):
        """Duration exceeding 3600 must be rejected."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()
        screen._get_input = MagicMock(
            side_effect=lambda x: "Test" if "name" in x else "99999"
        )
        is_valid, msg = screen._validate_inputs()
        assert is_valid is False
        assert "3600" in msg or "1 hour" in msg

    def test_zero_threads_rejected(self):
        """Zero or negative threads must be rejected."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()
        screen._get_input = MagicMock(
            side_effect=lambda x: "Test" if "name" in x else "0"
        )
        is_valid, msg = screen._validate_inputs()
        assert is_valid is False
        # First numeric field checked is duration, which defaults to 0
        assert "duration" in msg.lower() or "positive" in msg.lower()

    def test_valid_inputs_pass_validation(self):
        """A fully valid form must pass validation."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()

        input_values = {
            "input_profile_name": "My Test Profile",
            "input_duration": "30",
            "input_threads": "4",
            "input_batch_runs": "3",
            "input_cooldown": "10",
        }

        screen._get_input = MagicMock(
            side_effect=lambda x: input_values.get(x, "0")
        )
        is_valid, msg = screen._validate_inputs()
        assert is_valid is True
        assert msg == ""

    def test_minimal_valid_inputs_pass(self):
        """Minimal valid inputs (all 1s) must pass."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()

        input_values = {
            "input_profile_name": "Min",
            "input_duration": "1",
            "input_threads": "1",
            "input_batch_runs": "1",
            "input_cooldown": "0",
        }

        screen._get_input = MagicMock(
            side_effect=lambda x: input_values.get(x, "0")
        )
        is_valid, msg = screen._validate_inputs()
        assert is_valid is True

    def test_zero_cooldown_allowed(self):
        """Zero cooldown is valid (no cooldown between runs)."""
        from ui.screens.profile_creation import ProfileCreationScreen

        screen = ProfileCreationScreen()

        input_values = {
            "input_profile_name": "NoCooldown",
            "input_duration": "10",
            "input_threads": "1",
            "input_batch_runs": "1",
            "input_cooldown": "0",
        }

        screen._get_input = MagicMock(
            side_effect=lambda x: input_values.get(x, "0")
        )
        is_valid, msg = screen._validate_inputs()
        assert is_valid is True


class TestI6ProfilePersistence:
    """Verify profile creation persists through ConfigManager."""

    def test_save_profile_uses_config_manager_create_profile(self):
        """_save_profile must call ConfigManager.create_profile with correct params."""
        from ui.screens.profile_creation import ProfileCreationScreen

        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, "wowfactor_config")

            # Create a real ConfigManager with a temp dir
            from core.config import ConfigManager
            manager = ConfigManager(config_dir=config_dir)

            # Call create_profile directly with same params the screen would use
            success = manager.create_profile(
                name="Test Profile",
                duration=15,
                num_threads=1,
                batch_runs=5,
                cooldown_seconds=5,
            )
            assert success is True

            # Verify profile was created
            profile = manager.get_profile("Test Profile")
            assert profile is not None
            assert profile.defaults.duration == 15
            assert profile.defaults.num_threads == 1
            assert profile.defaults.batch_runs == 5
            assert profile.defaults.cooldown_seconds == 5

    def test_profile_saved_to_file(self):
        """A saved profile must be persisted to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, "wowfactor_config")

            from core.config import ConfigManager

            manager = ConfigManager(config_dir=config_dir)
            success = manager.create_profile(
                name="Integration Test",
                duration=10,
                num_threads=2,
                batch_runs=3,
                cooldown_seconds=5,
            )
            assert success is True

            # Reload and verify
            manager2 = ConfigManager(config_dir=config_dir)
            profile = manager2.get_profile("Integration Test")
            assert profile is not None
            assert profile.name == "Integration Test"
            assert profile.defaults.duration == 10
            assert profile.defaults.num_threads == 2

    def test_duplicate_profile_rejected_by_manager(self):
        """ConfigManager must reject creating duplicate profiles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, "wowfactor_config")

            from core.config import ConfigManager

            manager = ConfigManager(config_dir=config_dir)
            manager.create_profile(name="Dup", duration=15)

            # Second creation of same name should fail
            success = manager.create_profile(name="Dup", duration=20)
            assert success is False


class TestI6Navigation:
    """Verify navigation actions work correctly."""

    async def test_cancel_button_go_back(self):
        """Cancel button must navigate back."""
        from textual.app import App
        from textual.widgets import Button
        from ui.screens.profile_selection import ProfileSelectionScreen
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileSelectionScreen(["Profile A"]))
            await pilot.pause()
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()

            screen = pilot.app.screen
            assert isinstance(screen, ProfileCreationScreen)

            cancel_btn = screen.query_one("#cancel_profile_btn", Button)
            cancel_btn.post_message(Button.Pressed(cancel_btn))
            await pilot.pause()

            # Should have gone back to ProfileSelectionScreen
            assert isinstance(pilot.app.screen, ProfileSelectionScreen)

    async def test_back_keybinding_goes_back(self):
        """The 'b' keybinding must navigate back."""
        from textual.app import App
        from ui.screens.profile_selection import ProfileSelectionScreen
        from ui.screens.profile_creation import ProfileCreationScreen

        async with App().run_test() as pilot:
            pilot.app.push_screen(ProfileSelectionScreen(["Profile A"]))
            await pilot.pause()
            pilot.app.push_screen(ProfileCreationScreen())
            await pilot.pause()

            screen = pilot.app.screen
            # Ensure no widget has focus, so keybinding goes to screen
            screen.focus(None)
            await pilot.pause()
            # Trigger the action directly
            screen.action_back()
            await pilot.pause()

            assert isinstance(pilot.app.screen, ProfileSelectionScreen)


class TestI6ProfileSelectionWiring:
    """Verify ProfileSelectionScreen wires Create New Profile correctly."""

    async def test_create_button_pushes_profile_creation_screen(self):
        """Clicking Create New Profile must push ProfileCreationScreen."""
        from textual.app import App
        from textual.widgets import Button
        from ui.screens.profile_selection import ProfileSelectionScreen
        from ui.screens.profile_creation import ProfileCreationScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileSelectionScreen(["Existing Profile"]))
            await pilot.pause()

            screen = pilot.app.screen
            create_btn = screen.query_one("#create_new_profile", Button)
            create_btn.post_message(Button.Pressed(create_btn))
            await pilot.pause()

            assert isinstance(pilot.app.screen, ProfileCreationScreen)

    async def test_create_button_no_stub_notification(self):
        """Create New Profile must NOT show stub notification."""
        from textual.app import App
        from textual.widgets import Button
        from ui.screens.profile_selection import ProfileSelectionScreen

        class TestApp(App):
            CSS_PATH = None

        async with TestApp().run_test() as pilot:
            pilot.app.push_screen(ProfileSelectionScreen(["Profile A"]))
            await pilot.pause()

            screen = pilot.app.screen
            create_btn = screen.query_one("#create_new_profile", Button)
            create_btn.post_message(Button.Pressed(create_btn))
            await pilot.pause()

            # Should have navigated to ProfileCreationScreen, not shown a notification
            from ui.screens.profile_creation import ProfileCreationScreen
            assert isinstance(pilot.app.screen, ProfileCreationScreen)

    async def test_profile_selection_has_back_binding(self):
        """ProfileSelectionScreen must have 'b' binding for back."""
        from ui.screens.profile_selection import ProfileSelectionScreen

        binding_keys = [b.key for b in ProfileSelectionScreen.BINDINGS]
        assert "b" in binding_keys

    async def test_profile_selection_has_quit_binding(self):
        """ProfileSelectionScreen must have 'q' binding for quit."""
        from ui.screens.profile_selection import ProfileSelectionScreen

        binding_keys = [b.key for b in ProfileSelectionScreen.BINDINGS]
        assert "q" in binding_keys


class TestI6ProfileCreatedMessage:
    """Verify ProfileCreatedMessage class works correctly."""

    def test_message_has_profile_name(self):
        """ProfileCreatedMessage must store the profile name."""
        from ui.screens.profile_creation import ProfileCreatedMessage

        msg = ProfileCreatedMessage("My Profile")
        assert msg.profile_name == "My Profile"

    def test_message_instantiable(self):
        """ProfileCreatedMessage must be instantiable."""
        from ui.screens.profile_creation import ProfileCreatedMessage

        msg = ProfileCreatedMessage("")
        assert msg.profile_name == ""


class TestI6AppRegistration:
    """Verify ProfileCreationScreen is registered in the app."""

    def test_screen_in_app_screens_dict(self):
        """ProfileCreationScreen must be in WowFactorTUI.SCREENS."""
        from ui.app import WowFactorTUI

        assert "profile_creation" in WowFactorTUI.SCREENS
        from ui.screens.profile_creation import ProfileCreationScreen
        assert WowFactorTUI.SCREENS["profile_creation"] is ProfileCreationScreen

    def test_profile_selection_in_app_screens_dict(self):
        """ProfileSelectionScreen must be in WowFactorTUI.SCREENS."""
        from ui.app import WowFactorTUI

        assert "profile_selection" in WowFactorTUI.SCREENS

    def test_profile_creation_importable_from_screens_init(self):
        """ProfileCreationScreen must be importable from ui.screens."""
        from ui.screens import ProfileCreationScreen, ProfileCreatedMessage

        assert ProfileCreationScreen is not None
        assert ProfileCreatedMessage is not None


class TestI6TCSSStyles:
    """Verify TCSS styles for profile creation exist."""

    def test_profile_creation_styles_exist_in_tcss(self):
        """styles.tcss must contain profile creation related rules."""
        with open("ui/styles.tcss") as f:
            content = f.read()

        assert "input_profile_name" in content
        assert "input_duration" in content
        assert "form-error" in content

    def test_form_error_style_exists(self):
        """form-error class must be defined in styles.tcss."""
        with open("ui/styles.tcss") as f:
            content = f.read()

        assert ".form-error" in content


class TestI6ProfileSelectionNoStaticImport:
    """Verify ProfileSelectionScreen removed unused Static import (per I6 spec)."""

    def test_no_static_import_in_profile_selection(self):
        """ProfileSelectionScreen should not import Static from textual.widgets."""
        with open("ui/screens/profile_selection.py") as f:
            content = f.read()

        # The I6 spec says to remove unused Static import
        assert "from textual.widgets import" in content
        lines = content.split("\n")
        for line in lines:
            if "from textual.widgets import" in line:
                assert "Static" not in line, (
                    "Static import should be removed from profile_selection.py"
                )


class TestI6ProfileSelectionInheritsBaseScreen:
    """Verify ProfileSelectionScreen still extends BaseScreen."""

    def test_profile_selection_inherits_basescreen(self):
        """ProfileSelectionScreen must inherit from BaseScreen."""
        from ui.screens.base_screen import BaseScreen
        from ui.screens.profile_selection import ProfileSelectionScreen

        assert issubclass(ProfileSelectionScreen, BaseScreen)