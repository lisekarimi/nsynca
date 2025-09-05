# gui/results_display.py
"""
Handles formatting and displaying update results in table format.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Dict


class ResultsDisplay:
    """Manages the results display area."""

    def __init__(self, parent_frame: ctk.CTkFrame):
        # Create results section
        self.frame = ctk.CTkFrame(parent_frame)
        self.frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Title
        self.title_label = ctk.CTkLabel(
            self.frame, text="Update Results", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.title_label.pack(pady=10)

        # Results text area
        self.results_text = ctk.CTkTextbox(
            self.frame, font=ctk.CTkFont(family="Consolas", size=14), height=300
        )
        self.results_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def clear(self):
        """Clear the results display."""
        self.results_text.delete("1.0", "end")

    def show_results(self, run_data: Dict):
        """Display results in a table format."""
        self.clear()

        # Header
        self.results_text.insert(
            "end", f"Update Summary - {run_data['type'].upper()}\n"
        )
        self.results_text.insert(
            "end",
            f"Time: {datetime.fromisoformat(run_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n",
        )
        self.results_text.insert("end", f"{'=' * 70}\n\n")

        # Display each project and its updates
        projects = run_data["projects_updated"]

        for project_name, updates in projects.items():
            # Project header
            self.results_text.insert("end", f"{project_name}\n")

            # Display updates in order based on what was updated
            # Deployment info first
            if "Last Dev" in updates:
                self.results_text.insert("end", f"  Last Dev:  {updates['Last Dev']}\n")
            if "Last Prod" in updates:
                self.results_text.insert(
                    "end", f"  Last Prod: {updates['Last Prod']}\n"
                )

            # Release counts
            if "Dev Releases" in updates:
                self.results_text.insert(
                    "end", f"  Dev Releases: {updates['Dev Releases']}\n"
                )
            if "Prod Releases" in updates:
                self.results_text.insert(
                    "end", f"  Prod Releases: {updates['Prod Releases']}\n"
                )

            # Task info
            if "Total Tasks" in updates:
                self.results_text.insert(
                    "end", f"  Total Tasks: {updates['Total Tasks']}\n"
                )
            if "Completed Tasks" in updates:
                self.results_text.insert(
                    "end", f"  Completed Tasks: {updates['Completed Tasks']}\n"
                )

            # Add spacing between projects
            self.results_text.insert("end", "\n")

        # Summary
        self.results_text.insert("end", f"{'-' * 70}\n")
        self.results_text.insert("end", f"Total: {len(projects)} projects updated\n")
