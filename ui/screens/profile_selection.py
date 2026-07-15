"""Profile Selection Screen for WowFactor TUI.

Provides interface for selecting or creating benchmark profiles.
"""

from textual.widgets import Button, Static, Label
from textual.containers import Container, Vertical
from typing import List

from .base_screen import BaseScreen


class ProfileSelectionScreen(BaseScreen):
    """Screen for selecting an existing profile or creating a new one."""
    
    def __init__(self, profiles: List[str], create_new: bool = False) -> None:
        super().__init__()
        self.profiles = profiles
        self.create_new = create_new
    
    def compose(self) -> "ComposeResult":
        with Container(classes="profile-selection-container"):
            yield Label("Select a Benchmark Profile", id="profile-title")
            
            if self.create_new or not self.profiles:
                # Show option to create new profile
                yield Button("Create New Profile", id="create_new_profile", variant="primary", classes="action-btn")
            else:
                # Show list of existing profiles
                for profile in self.profiles:
                    yield Button(profile, id=f"select_{profile}", variant="default", classes="action-btn")
                
                if not self.create_new:
                    yield Button("Create New Profile", id="create_new_profile", variant="primary", classes="action-btn")
            
            yield Button("Cancel", id="cancel_selection", variant="default", classes="action-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "create_new_profile":
            # Navigate to profile creation screen (placeholder)
            self.app.notify("Profile creation not yet implemented", title="Info")
            event.stop()
        elif event.button.id.startswith("select_"):
            selected = event.button.id.replace("select_", "")
            self.app.notify(f"Selected profile: {selected}", title="Profile Selected")
            # Pop this screen to return to previous
            if len(self.app.screen_stack) > 1:
                self.navigation.go_back()
            event.stop()
        elif event.button.id == "cancel_selection":
            if len(self.app.screen_stack) > 1:
                self.navigation.go_back()
            event.stop()
