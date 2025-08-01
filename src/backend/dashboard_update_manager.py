import logging
from typing import Dict, Any, Callable
import asyncio

class DashboardUpdateManager:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.update_callbacks = []

    def add_widget_to_main_dashboard(self, widget_data: Dict[str, Any]):
        self.logger.info(f"Adding widget to main dashboard: {widget_data}")
        # Placeholder for adding a widget to the main dashboard
        self.trigger_dashboard_update()

    def add_web_view_to_dashboard(self, view_data: Dict[str, Any]):
        self.logger.info(f"Adding web view to dashboard: {view_data}")
        # Placeholder for adding a web view to a dashboard
        self.trigger_dashboard_update()

    def update_main_dashboard_with_new_features(self, feature_data: Dict[str, Any]):
        self.logger.info(f"Updating main dashboard with new features: {feature_data}")
        # Placeholder for updating the main dashboard with new features
        self.trigger_dashboard_update()

    def register_dashboard_update_callback(self, callback: Callable):
        """Registers a callback function to be called when the dashboard needs to update."""
        self.update_callbacks.append(callback)

    def trigger_dashboard_update(self):
        """Triggers the dashboard update by calling all registered callbacks asynchronously."""
        for callback in self.update_callbacks:
            asyncio.create_task(self._async_trigger_callback(callback))

    async def _async_trigger_callback(self, callback: Callable):
        """Calls the dashboard update callback asynchronously."""
        try:
            await callback()
        except Exception as e:
            self.logger.error(f"Error during dashboard update callback: {e}")
