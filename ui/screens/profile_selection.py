"""Profile Selection Screen for WowFactor TUI.

Provides interface for selecting or creating benchmark profiles.
"""

import re
from typing import List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Label
from textual.containers import Container

from .base_screen import BaseScreen
from .profile_creation import ProfileCreationScreen, ProfileCreatedMessage


class ProfileSelectionScreen(BaseScreen):
    """Screen for selecting an existing profile or creating a new one."""

    BINDINGS = [
        Binding("b", "back", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, profiles: List[str], create_new: bool = False) -> None:
        super().__init__()
        self.profiles = profiles
        self.create_new = create_new
        self._profile_id_map: dict[str, str] = {}

    @staticmethod
    def _sanitize_id(name: str) -> str:
        """Sanitize a profile name into a valid CSS identifier."""
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized or '_unnamed'

    def compose(self) -> ComposeResult:
        self._profile_id_map = {}
        with Container(classes="profile-selection-container"):
            yield Label("Select a Benchmark Profile", id="profile-title")

            if self.create_new or not self.profiles:
                yield Button("Create New Profile", id="create_new_profile", variant="primary", classes="action-btn")
            else:
                for profile in self.profiles:
                    safe_id = f"select_{self._sanitize_id(profile)}"
                    self._profile_id_map[safe_id] = profile
                    yield Button(profile, id=safe_id, variant="default", classes="action-btn")

                if not self.create_new:
                    yield Button("Create New Profile", id="create_new_profile", variant="primary", classes="action-btn")

            yield Button("Cancel", id="cancel_selection", variant="default", classes="action-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create_new_profile":
            self.on_create_profile()
            event.stop()
        elif event.button.id in self._profile_id_map:
            selected = self._profile_id_map[event.button.id]
            self.app.notify(f"Selected profile: {selected}", title="Profile Selected")
            if len(self.app.screen_stack) > 1:
                self.navigation.go_back()
            event.stop()
        elif event.button.id.startswith("select_"):
            selected = event.button.id.replace("select_", "")
            self.app.notify(f"Selected profile: {selected}", title="Profile Selected")
            if len(self.app.screen_stack) > 1:
                self.navigation.go_back()
            event.stop()
        elif event.button.id == "cancel_selection":
            if len(self.app.screen_stack) > 1:
                self.navigation.go_back()
            event.stop()

    def on_create_profile(self) -> None:
        """Navigate to the profile creation screen."""
        self.app.push_screen(ProfileCreationScreen())

    def on_profile_created(self, message: ProfileCreatedMessage) -> None:
        """Refresh the profile list when a new profile is created."""
        self.app.notify(f"Profile '{message.profile_name}' created.", title="Profile Created")
        # Reload profiles from ConfigManager
        try:
            from core.config import ConfigManager
            manager = ConfigManager()
            self.profiles = list(manager.get_all_profiles().keys())
            self.refresh(layout=True)
        except Exception:
            pass

    def action_back(self) -> None:
        """Go back to the previous screen."""
        if len(self.app.screen_stack) > 1:
            self.navigation.go_back()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
