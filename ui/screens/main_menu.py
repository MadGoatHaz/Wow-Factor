from textual.widgets import Button, Footer, Static
from textual.containers import Container

# Import shared components to avoid circular imports
from ui.shared import WowFactorHeader, RETRO_GRADIENT_COLORS, colorize_text_gradient

# Import constants from core
from core.benchmark import BENCHMARK_DIR

from .base_screen import BaseScreen


class MainMenuScreen(BaseScreen):
    BINDINGS = [
        ("q", "quit_app", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(classes="main-menu-container"):
            yield WowFactorHeader(id="app-header")
            with Container(classes="menu-grid"):
                yield Button("Run New Benchmark", id="run_single_benchmark", variant="primary", classes="action-btn")
                yield Button("Run Batch Benchmark", id="run_batch_benchmark", variant="primary", classes="action-btn")
                yield Button("View Best Score per Machine", id="view_best_scores", variant="primary", classes="action-btn")
                yield Button("Compare a Specific CPU", id="compare_cpu", variant="primary", classes="action-btn")
                yield Button("View All Scores (Full List)", id="view_all_scores", variant="primary", classes="action-btn")
                yield Button("View Analytics", id="view_analytics", variant="primary", classes="action-btn")
                yield Button("View Trends", id="view_trends", variant="primary", classes="action-btn")
                yield Button("Clear Invalid Scores", id="clear_invalid_confirm", variant="error", classes="action-btn")
                yield Button("Manage Profiles", id="manage_profiles", variant="primary", classes="action-btn")
                yield Button("Quit", id="quit_app", variant="default", classes="action-btn")
            yield Static("Awaiting command>", id="command_prompt")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#app-header", WowFactorHeader).update_title("BENCHMARK INTERFACE")

    def action_quit_app(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses on this screen."""
        if event.button.id == "quit_app":
            self.action_quit_app()
        elif event.button.id == "run_single_benchmark":
            self.navigation.navigate_to("run_single_benchmark")
            event.stop() # Stop event propagation
        elif event.button.id == "run_batch_benchmark":
            self.navigation.navigate_to("run_batch_benchmark")
            event.stop() # Stop event propagation
        elif event.button.id == "view_best_scores":
            self.navigation.navigate_to("view_best_scores")
            event.stop() # Stop event propagation
        elif event.button.id == "view_all_scores":
            self.navigation.navigate_to("view_all_scores")
            event.stop() # Stop event propagation
        elif event.button.id == "clear_invalid_confirm":
            # Check how many invalid files exist before showing confirmation
            import os
            if not os.path.exists(BENCHMARK_DIR):
                invalid_count = 0
            else:
                # Count all JSON files and check which ones are invalid
                import json
                invalid_count = 0
                for filename in os.listdir(BENCHMARK_DIR):
                    if filename.endswith('.json'):
                        try:
                            with open(os.path.join(BENCHMARK_DIR, filename), 'r') as f:
                                data = json.load(f)
                                # Check if it has required fields
                                if 'ops_per_second' not in data or 'system' not in data or 'processor_model' not in data.get('system', {}):
                                    invalid_count += 1
                        except (json.JSONDecodeError, KeyError):
                            invalid_count += 1
            self.navigation.navigate_to("clear_invalid_confirm", invalid_count=invalid_count)
            event.stop() # Stop event propagation
        elif event.button.id == "manage_profiles":
            from core.config import config_manager, BenchmarkProfile
            profiles = config_manager.get_all_profiles()
            profile_names = list(profiles.keys())
            
            if not profile_names:
                self.navigation.navigate_to("profile_selection", create_new=True)
            else:
                self.navigation.navigate_to("profile_selection", profiles=profile_names)
            event.stop() # Stop event propagation
        elif event.button.id == "compare_cpu":
            self.navigation.navigate_to("compare_cpu")
            event.stop() # Stop event propagation
        elif event.button.id == "view_analytics":
            self.navigation.navigate_to("analytics")
            event.stop()
        elif event.button.id == "view_trends":
            self.navigation.navigate_to("trends_chart")
            event.stop()
        else: # For other buttons, replace direct prompt update with notification service
            self.navigation.notify(f"Command: {event.button.label} selected", type="info")
            event.stop() # Stop event propagation for other buttons too
