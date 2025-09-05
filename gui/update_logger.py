# gui/update_logger.py
"""
Tracks and saves update history to JSON files.
"""

import os
import json
from datetime import datetime
from typing import Dict


class UpdateLogger:
    """Tracks updates for reporting and history."""

    def __init__(self):
        self.updates = []
        self.current_run = {
            "timestamp": None,
            "type": None,
            "status": "pending",
            "projects_updated": {},
        }

    def start_run(self, update_type: str):
        """Start tracking a new run."""
        self.current_run = {
            "timestamp": datetime.now().isoformat(),
            "type": update_type,
            "status": "running",
            "projects_updated": {},
        }

    def add_project_update(self, project_name: str, updates: Dict):
        """Add a project update to current run."""
        # Process the updates to create clean format
        clean_updates = {}

        for key, value in updates.items():
            # Handle version fields with dates
            if (
                key == "Last Dev Version"
                and isinstance(value, dict)
                and "rich_text" in value
            ):
                version = self._extract_text(value)
                date = self._extract_date(updates.get("Last Dev Deploy", {}))
                if version != "N/A":  # Only add if there's a version
                    clean_updates["Last Dev"] = f"{version} @ {date}"
            elif (
                key == "Last Prod Version"
                and isinstance(value, dict)
                and "rich_text" in value
            ):
                version = self._extract_text(value)
                date = self._extract_date(updates.get("Last Prod Deploy", {}))
                if version != "N/A":  # Only add if there's a version
                    clean_updates["Last Prod"] = f"{version} @ {date}"
            # Handle number fields
            elif (
                key == "Nb Dev Releases"
                and isinstance(value, dict)
                and "number" in value
            ):
                clean_updates["Dev Releases"] = value["number"]
            elif (
                key == "Nb Prod Releases"
                and isinstance(value, dict)
                and "number" in value
            ):
                clean_updates["Prod Releases"] = value["number"]
            elif key == "Total Tasks" and isinstance(value, dict) and "number" in value:
                clean_updates["Total Tasks"] = value["number"]
            elif (
                key == "Completed Tasks"
                and isinstance(value, dict)
                and "number" in value
            ):
                clean_updates["Completed Tasks"] = value["number"]
            # Skip date fields as they're already combined with versions
            elif key in ["Last Dev Deploy", "Last Prod Deploy"]:
                continue

        # Store or merge the clean updates
        if project_name not in self.current_run["projects_updated"]:
            self.current_run["projects_updated"][project_name] = clean_updates
        else:
            self.current_run["projects_updated"][project_name].update(clean_updates)

    def _extract_text(self, value: Dict) -> str:
        """Extract text from rich_text field."""
        if value.get("rich_text") and len(value["rich_text"]) > 0:
            return value["rich_text"][0]["text"]["content"]
        return "N/A"

    def _extract_date(self, value: Dict) -> str:
        """Extract date from date field."""
        if isinstance(value, dict) and "date" in value and value["date"]:
            return value["date"]["start"][:10]
        return "N/A"

    def finish_run(self, success: bool = True) -> Dict:
        """Finish current run and save to history."""
        self.current_run["status"] = "success" if success else "failed"
        self.current_run["completed_at"] = datetime.now().isoformat()
        self.updates.append(self.current_run)
        self.save_to_file()
        return self.current_run

    def save_to_file(self):
        """Save update history to JSON file."""
        os.makedirs("logs", exist_ok=True)
        filename = f"logs/update_history_{datetime.now().strftime('%Y%m')}.json"

        try:
            # Load existing data
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    existing = json.load(f)
            else:
                existing = []

            # Append new data
            existing.append(self.current_run)

            # Save
            with open(filename, "w") as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            print(f"Error saving log: {e}")
