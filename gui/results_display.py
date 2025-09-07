# gui/results_display.py
"""
Handles formatting and displaying update results in table format.
"""

import customtkinter as ctk
from typing import Dict
from gui.utils.run_data_parser import RunDataParser


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
        """Display results for projects and/or services."""
        self.clear()

        # Header using utility
        header = RunDataParser.format_header_info(run_data)
        self.results_text.insert("end", header)

        # Use utility to get proper data separation
        counts = RunDataParser.get_entity_counts(run_data)

        # -------- Projects section --------
        if RunDataParser.should_show_projects_section(run_data):
            self.results_text.insert(
                "end", f"Projects Updated ({counts['total_projects']}):\n"
            )
            self.results_text.insert("end", f"{'-' * 50}\n\n")

            for project_name, updates in counts["projects"].items():
                # Project header
                self.results_text.insert("end", f"{project_name}\n")

                # Deployment info
                if "Last Dev" in updates:
                    self.results_text.insert(
                        "end", f"  Last Dev:  {updates['Last Dev']}\n"
                    )
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

                self.results_text.insert("end", "\n")

        # -------- Charges section --------
        if RunDataParser.should_show_charges_section(run_data):
            # Add divider if we had projects above
            if counts["total_projects"] > 0:
                self.results_text.insert("end", "\n")

            self.results_text.insert(
                "end", f"Charges Created ({counts['total_charges']}):\n"
            )
            self.results_text.insert("end", f"{'-' * 50}\n\n")

            for charge_name, properties in counts["charges"].items():
                self.results_text.insert("end", f"{charge_name}\n")
                for key, value in properties.items():
                    self.results_text.insert("end", f"  {key}: {value}\n")
                self.results_text.insert("end", "\n")

        # -------- Services section --------
        if RunDataParser.should_show_services_section(run_data):
            # Add divider if we had projects above
            if counts["total_projects"] > 0:
                self.results_text.insert("end", "\n")

            services_to_show = RunDataParser.get_services_data_for_display(run_data)

            self.results_text.insert(
                "end", f"Services Updated ({counts['total_services']}):\n"
            )
            self.results_text.insert("end", f"{'-' * 50}\n\n")

            for service_name, updates in services_to_show.items():
                self.results_text.insert("end", f"{service_name}\n")
                for key, val in updates.items():
                    self.results_text.insert("end", f"  {key}: {val}\n")
                self.results_text.insert("end", "\n")

        # Summary footer using utility
        self.results_text.insert("end", f"{'-' * 70}\n")
        summary = RunDataParser.format_run_summary(run_data)
        self.results_text.insert("end", f"{summary}\n")
