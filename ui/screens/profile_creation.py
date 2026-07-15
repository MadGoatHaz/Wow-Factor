"""Profile Creation Screen for WowFactor TUI.

Provides a form for creating new benchmark profiles with validation.
Implements CHUNK-I6 from the GUI Rework Blueprint.
"""

from __future__ import annotations

import multiprocessing
from typing import TYPE_CHECKING

from textual import on
from textual.binding import Binding
from textual.containers import Container
from textual.app import ComposeResult
from textual.widgets import Button, Footer, Header, Input, Label

from .base_screen import BaseScreen


class ProfileCreatedMessage:
    """Posted when a new profile is successfully saved."""

    def __init__(self, profile_name: str) -> None:
        self.profile_name = profile_name


class ProfileCreationScreen(BaseScreen):
    """Screen for creating a new benchmark profile.

    Provides form fields for profile name, duration, threads, batch runs,
    and cooldown. Validates inputs and persists via ConfigManager.
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save Profile", show=True),
        Binding("b", "back", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    DEFAULT_CSS = """
    ProfileCreationScreen {
        align: center top;
        padding: 1 4;
    }

    #profile_form_container {
        width: 100%;
        max-width: 60;
        height: auto;
    }

    #profile_title {
        text-style: bold;
        margin-bottom: 1;
    }

    .form-field {
        margin-bottom: 1;
    }

    .form-field > Label {
        width: 16;
        margin-bottom: 0;
    }

    .form-field > Input {
        width: 1fr;
    }

    .form-error {
        color: red;
        text-style: italic;
        margin-top: 0;
        margin-bottom: 1;
        display: none;
    }

    .form-error.visible {
        display: block;
    }

    #profile_buttons {
        dock: bottom;
        width: 100%;
        content-align: center bottom;
        margin-bottom: 1;
    }

    #save_profile_btn {
        dock: right;
    }

    #cancel_profile_btn {
        dock: right;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._existing_profiles: set[str] = set()
        self._load_existing_profile_names()

    def _load_existing_profile_names(self) -> None:
        """Load existing profile names to prevent duplicates."""
        try:
            from core.config import ConfigManager

            manager = ConfigManager()
            self._existing_profiles = set(manager.get_all_profiles().keys())
        except Exception:
            self._existing_profiles = set()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="profile_form_container"):
            yield Label("Create New Benchmark Profile", id="profile_title")
            yield Label("")

            # Profile name field
            with Container(classes="form-field"):
                yield Label("Profile Name:")
                yield Input(placeholder="e.g., Quick Test", id="input_profile_name")

            # Duration field
            with Container(classes="form-field"):
                yield Label("Duration (sec):")
                yield Input(
                    placeholder="15",
                    id="input_duration",
                    type="integer",
                )

            # Threads field
            with Container(classes="form-field"):
                yield Label("Threads:")
                yield Input(
                    placeholder="1",
                    id="input_threads",
                    type="integer",
                )

            # Batch runs field
            with Container(classes="form-field"):
                yield Label("Batch Runs:")
                yield Input(
                    placeholder="5",
                    id="input_batch_runs",
                    type="integer",
                )

            # Cooldown field
            with Container(classes="form-field"):
                yield Label("Cooldown (sec):")
                yield Input(
                    placeholder="5",
                    id="input_cooldown",
                    type="integer",
                )

            # Error display area
            yield Label("", id="error_display", classes="form-error")

        # Action buttons
        with Container(id="profile_buttons"):
            yield Button("Cancel", id="cancel_profile_btn", variant="default")
            yield Button("Save", id="save_profile_btn", variant="primary")
        yield Footer()

    def _clear_error(self) -> None:
        """Hide and clear the error display."""
        try:
            error_widget = self.query_one("#error_display", Label)
            error_widget.update("")
            error_widget.classes = {"form-error"}
        except Exception:
            pass

    def _show_error(self, message: str) -> None:
        """Display an error message."""
        try:
            error_widget = self.query_one("#error_display", Label)
            error_widget.update(message)
            error_widget.classes = {"form-error", "visible"}
        except Exception:
            self.app.notify(message, severity="error")

    def _get_input(self, input_id: str) -> str:
        """Get the value from an input widget."""
        try:
            return self.query_one(f"#{input_id}", Input).value
        except Exception:
            return ""

    def _get_int_input(self, input_id: str, default: int = 0) -> int:
        """Get an integer value from an input widget."""
        value = self._get_input(input_id)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _validate_inputs(self) -> tuple[bool, str]:
        """Validate all form inputs.

        Returns:
            Tuple of (is_valid, error_message).
            If valid, error_message is empty.
        """
        # Profile name validation
        name = self._get_input("input_profile_name").strip()
        if not name:
            return False, "Profile name is required."
        if len(name) > 100:
            return False, "Profile name must be 100 characters or less."
        if name in self._existing_profiles:
            return False, f"A profile named '{name}' already exists."

        # Duration validation
        duration = self._get_int_input("input_duration")
        if duration <= 0:
            return False, "Duration must be a positive number."
        if duration > 3600:
            return False, "Duration must not exceed 3600 seconds (1 hour)."

        # Threads validation
        threads = self._get_int_input("input_threads")
        max_threads = multiprocessing.cpu_count() or 1
        if threads < 1:
            return False, "Threads must be at least 1."
        if threads > max_threads:
            return False, f"Threads cannot exceed available CPUs ({max_threads})."

        # Batch runs validation
        batch_runs = self._get_int_input("input_batch_runs")
        if batch_runs < 1:
            return False, "Batch runs must be at least 1."
        if batch_runs > 100:
            return False, "Batch runs must not exceed 100."

        # Cooldown validation
        cooldown = self._get_int_input("input_cooldown")
        if cooldown < 0:
            return False, "Cooldown must be 0 or greater."
        if cooldown > 300:
            return False, "Cooldown must not exceed 300 seconds (5 minutes)."

        return True, ""

    @on(Button.Pressed, "#save_profile_btn")
    def _handle_save(self, event: Button.Pressed) -> None:
        """Handle the save button press."""
        event.stop()
        self._clear_error()

        is_valid, error_msg = self._validate_inputs()
        if not is_valid:
            self._show_error(error_msg)
            return

        self._save_profile()

    def _save_profile(self) -> None:
        """Save the profile using ConfigManager."""
        name = self._get_input("input_profile_name").strip()
        duration = self._get_int_input("input_duration")
        threads = self._get_int_input("input_threads")
        batch_runs = self._get_int_input("input_batch_runs")
        cooldown = self._get_int_input("input_cooldown")

        try:
            manager = self.get_service("config")
            if manager is None:
                from core.config import ConfigManager
                manager = ConfigManager()

            success = manager.create_profile(
                name=name,
                duration=duration,
                num_threads=threads,
                batch_runs=batch_runs,
                cooldown_seconds=cooldown,
            )

            if success:
                self._existing_profiles.add(name)
                self.app.notify(
                    f"Profile '{name}' created successfully.",
                    title="Success",
                    severity="information",
                )
                # Post message and go back
                self.post_message(ProfileCreatedMessage(name))
                if len(self.app.screen_stack) > 1:
                    self.app.pop_screen()
            else:
                self._show_error(f"Failed to create profile '{name}'. It may already exist.")
        except Exception as e:
            self._show_error(f"Error saving profile: {e}")

    @on(Button.Pressed, "#cancel_profile_btn")
    def _handle_cancel(self, event: Button.Pressed) -> None:
        """Handle the cancel button press."""
        event.stop()
        self._go_back()

    def action_back(self) -> None:
        """Go back to the previous screen."""
        self._go_back()

    def action_save(self) -> None:
        """Trigger save action."""
        self._clear_error()
        is_valid, error_msg = self._validate_inputs()
        if not is_valid:
            self._show_error(error_msg)
            return
        self._save_profile()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def _go_back(self) -> None:
        """Navigate back to the previous screen."""
        if len(self.app.screen_stack) > 1:
            self.app.pop_screen()