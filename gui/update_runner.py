# gui/update_runner.py
"""
Handles running updates in background threads with progress tracking.
"""

import threading
import queue

# Import from parent directory
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.orchestrator import UpdaterType


class UpdateRunner:
    """Manages update execution in background threads."""

    def __init__(self, orchestrator, update_queue: queue.Queue):
        self.orchestrator = orchestrator
        self.update_queue = update_queue

    def run_update(self, update_type: str):
        """Run update in a separate thread."""
        thread = threading.Thread(
            target=self._execute_update, args=(update_type,), daemon=True
        )
        thread.start()

    def _execute_update(self, update_type: str):
        """Execute the update."""
        try:
            self.update_queue.put(("status", "Initializing..."))

            # Map to UpdaterType
            if update_type == "all":
                updater_types = [UpdaterType.ALL]
            elif update_type == "deployment":
                updater_types = [UpdaterType.DEPLOYMENT]
            elif update_type == "task":
                updater_types = [UpdaterType.TASK]
            elif update_type == "charge":
                updater_types = [UpdaterType.CHARGE]
            elif update_type == "service":
                updater_types = [UpdaterType.SERVICE]
            else:
                raise ValueError(f"Unknown update_type: {update_type}")

            self.update_queue.put(("status", f"Running {update_type} update..."))

            # Run update
            self.orchestrator.run(updater_types)

            # Signal completion
            self.update_queue.put(("complete", "success"))

        except Exception as e:
            self.update_queue.put(("complete", f"error: {str(e)}"))
