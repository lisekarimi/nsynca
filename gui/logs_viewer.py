"""
Logs viewer tab for displaying update history.
"""

import customtkinter as ctk
import json
import os
from datetime import datetime
from typing import Dict, List


class LogsViewer:
    """Manages the logs viewing tab."""

    def __init__(self, parent_frame: ctk.CTkFrame):
        self.parent = parent_frame
        self.current_logs = []

        # Create widgets
        self.create_widgets()

        # Load initial logs
        self.refresh_logs()

    def create_widgets(self):
        """Create all widgets for logs viewer."""
        # Top controls frame
        controls_frame = ctk.CTkFrame(self.parent)
        controls_frame.pack(fill="x", padx=10, pady=10)

        # Month selector
        ctk.CTkLabel(
            controls_frame, text="Select Month:", font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=5)

        self.month_var = ctk.StringVar()
        self.month_dropdown = ctk.CTkOptionMenu(
            controls_frame,
            values=self.get_available_months(),
            variable=self.month_var,
            command=self.on_month_changed,
            width=150,
        )
        self.month_dropdown.pack(side="left", padx=5)

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            controls_frame, text="Refresh", command=self.refresh_logs, width=100
        )
        self.refresh_btn.pack(side="left", padx=20)

        # Filter by type
        ctk.CTkLabel(controls_frame, text="Filter:", font=ctk.CTkFont(size=14)).pack(
            side="left", padx=(20, 5)
        )

        self.filter_var = ctk.StringVar(value="all")
        self.filter_dropdown = ctk.CTkOptionMenu(
            controls_frame,
            values=["all", "deployment", "task", "success", "failed"],
            variable=self.filter_var,
            command=self.apply_filter,
            width=120,
        )
        self.filter_dropdown.pack(side="left", padx=5)

        # Main content area with two panes
        content_frame = ctk.CTkFrame(self.parent)
        content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Left pane - list of runs
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            left_frame, text="Update Runs", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        # Scrollable frame for runs list
        self.runs_scroll = ctk.CTkScrollableFrame(left_frame, width=350)
        self.runs_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Right pane - details
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            right_frame, text="Details", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)

        self.details_text = ctk.CTkTextbox(
            right_frame, font=ctk.CTkFont(family="Consolas", size=14), width=400
        )
        self.details_text.pack(fill="both", expand=True, padx=5, pady=5)

    def get_available_months(self) -> List[str]:
        """Get list of available log files."""
        months = []
        if os.path.exists("logs"):
            for file in os.listdir("logs"):
                if file.startswith("update_history_") and file.endswith(".json"):
                    # Extract YYYYMM from filename
                    month = file.replace("update_history_", "").replace(".json", "")
                    months.append(month)

        # Sort in reverse order (newest first)
        months.sort(reverse=True)

        # Format for display (YYYY-MM)
        formatted = []
        for m in months:
            if len(m) == 6:  # YYYYMM format
                formatted.append(f"{m[:4]}-{m[4:]}")

        return formatted if formatted else ["No logs found"]

    def on_month_changed(self, selected: str):
        """Handle month selection change."""
        self.load_logs_for_month(selected)

    def load_logs_for_month(self, month_display: str):
        """Load logs for selected month."""
        if month_display == "No logs found":
            return

        # Convert display format back to filename format
        month = month_display.replace("-", "")
        filename = f"logs/update_history_{month}.json"

        try:
            with open(filename, "r") as f:
                self.current_logs = json.load(f)
            self.display_runs()
        except Exception as e:
            print(f"Error loading logs: {e}")
            self.current_logs = []

    def display_runs(self):
        """Display all runs in the left pane."""
        # Clear existing widgets
        for widget in self.runs_scroll.winfo_children():
            widget.destroy()

        # Apply filter
        filtered_logs = self.filter_logs()

        # Display each run
        for i, run in enumerate(filtered_logs):
            run_frame = ctk.CTkFrame(self.runs_scroll)
            run_frame.pack(fill="x", pady=2)

            # Format timestamp
            timestamp = datetime.fromisoformat(run["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # Status indicator
            status_color = "green" if run["status"] == "success" else "red"
            status_text = "✓" if run["status"] == "success" else "✗"

            # Create run button
            btn_text = f"{status_text} {time_str} - {run['type'].upper()} - {len(run['projects_updated'])} projects"

            run_btn = ctk.CTkButton(
                run_frame,
                text=btn_text,
                command=lambda r=run: self.show_run_details(r),
                fg_color="transparent",
                text_color=status_color,
                hover_color=("gray75", "gray25"),
                anchor="w",
            )
            run_btn.pack(fill="x", padx=5, pady=2)

    def filter_logs(self) -> List[Dict]:
        """Apply current filter to logs."""
        filter_value = self.filter_var.get()

        if filter_value == "all":
            return self.current_logs
        elif filter_value in ["deployment", "task"]:
            return [log for log in self.current_logs if log["type"] == filter_value]
        elif filter_value in ["success", "failed"]:
            return [log for log in self.current_logs if log["status"] == filter_value]
        else:
            return self.current_logs

    def apply_filter(self, _):
        """Apply filter and refresh display."""
        self.display_runs()

    def show_run_details(self, run: Dict):
        """Show details of selected run in right pane."""
        self.details_text.delete("1.0", "end")

        # Header info
        timestamp = datetime.fromisoformat(run["timestamp"])
        self.details_text.insert("end", "Run Details\n")
        self.details_text.insert("end", "=" * 50 + "\n\n")
        self.details_text.insert(
            "end", f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        self.details_text.insert("end", f"Type: {run['type'].upper()}\n")
        self.details_text.insert("end", f"Status: {run['status']}\n")

        if "completed_at" in run:
            completed = datetime.fromisoformat(run["completed_at"])
            duration = (completed - timestamp).total_seconds()
            self.details_text.insert("end", f"Duration: {duration:.1f} seconds\n")

        self.details_text.insert(
            "end", f"\nProjects Updated ({len(run['projects_updated'])}):\n"
        )
        self.details_text.insert("end", f"{'-' * 50}\n\n")

        # Project details
        for project_name, updates in run["projects_updated"].items():
            self.details_text.insert("end", f"{project_name}\n")

            for key, value in updates.items():
                self.details_text.insert("end", f"  {key}: {value}\n")

            self.details_text.insert("end", "\n")

    def refresh_logs(self):
        """Refresh the logs display."""
        # Update months dropdown
        months = self.get_available_months()
        self.month_dropdown.configure(values=months)

        # Load most recent month
        if months and months[0] != "No logs found":
            self.month_var.set(months[0])
            self.load_logs_for_month(months[0])
        else:
            self.current_logs = []
            self.display_runs()
