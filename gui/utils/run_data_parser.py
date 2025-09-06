# gui/utils/run_data_parser.py
"""
Shared utilities for parsing and formatting run data between results display and logs viewer.
"""

from typing import Dict, Tuple
from datetime import datetime


class RunDataParser:
    """Handles parsing and formatting of run data for consistent display."""

    @staticmethod
    def separate_projects_and_services(run_data: Dict) -> Tuple[Dict, Dict]:
        """
        Separate mixed project/service data into proper categories.
        Returns (actual_projects, actual_services).
        """
        projects = run_data.get("projects_updated", {}) or {}
        services = run_data.get("services_updated", {}) or {}
        run_type = run_data.get("type")

        if run_type == "all":
            # For "all" runs, separate mixed data based on content
            actual_projects = {}
            actual_services = {}

            # Separate based on data structure
            for name, updates in projects.items():
                if any(
                    key in updates
                    for key in [
                        "Last Dev",
                        "Last Prod",
                        "Dev Releases",
                        "Prod Releases",
                        "Total Tasks",
                        "Completed Tasks",
                    ]
                ):
                    actual_projects[name] = updates
                else:
                    actual_services[name] = updates

            # Add any correctly placed services
            actual_services.update(services)

            return actual_projects, actual_services
        else:
            return projects, services

    @staticmethod
    def get_entity_counts(run_data: Dict) -> Dict:
        """
        Get counts for projects and services with proper separation.
        Returns dict with 'projects', 'services', 'total_projects', 'total_services'.
        """
        actual_projects, actual_services = RunDataParser.separate_projects_and_services(
            run_data
        )
        charges = run_data.get("charges_created", {}) or {}
        run_type = run_data.get("type")

        # For service-only runs, check if data is in wrong bucket
        if run_type == "service" and not actual_services and actual_projects:
            actual_services = actual_projects
            actual_projects = {}

        return {
            "projects": actual_projects,
            "charges": charges,
            "services": actual_services,
            "total_projects": len(actual_projects),
            "total_charges": len(charges),
            "total_services": len(actual_services),
        }

    @staticmethod
    def format_run_summary(run_data: Dict) -> str:
        """Format run summary text for display."""
        counts = RunDataParser.get_entity_counts(run_data)
        run_type = run_data.get("type")

        if run_type == "charge":
            return f"Total: {counts['total_charges']} charges created"
        elif run_type == "service":
            return f"Total: {counts['total_services']} services updated"
        elif run_type in ("deployment", "task", "project"):
            return f"Total: {counts['total_projects']} projects updated"
        else:  # "all"
            return f"Total: {counts['total_projects']} projects, {counts['total_services']} services, {counts['total_charges']} charges"

    @staticmethod
    def format_button_text(run_data: Dict, timestamp_str: str, status_text: str) -> str:
        """Format button text for logs viewer list."""
        counts = RunDataParser.get_entity_counts(run_data)
        run_type = run_data.get("type", "")

        if run_type == "charge":
            entity_text = f"{counts['total_charges']} charges"
        elif run_type == "service":
            entity_text = f"{counts['total_services']} services"
        elif run_type == "all":
            entity_text = f"{counts['total_projects']} projects, {counts['total_services']} services, {counts['total_charges']} charges"
        else:
            entity_text = f"{counts['total_projects']} projects"

        return f"{status_text} {timestamp_str} - {run_type.upper()} - {entity_text}"

    @staticmethod
    def format_header_info(run_data: Dict) -> str:
        """Format header information for details view."""
        timestamp = datetime.fromisoformat(run_data["timestamp"])
        header = f"Update Summary - {run_data['type'].upper()}\n"
        header += f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"{'=' * 70}\n\n"
        return header

    @staticmethod
    def should_show_projects_section(run_data: Dict) -> bool:
        """Determine if projects section should be shown."""
        run_type = run_data.get("type")
        counts = RunDataParser.get_entity_counts(run_data)
        return (
            run_type in ("deployment", "task", "project", "all")
            and counts["total_projects"] > 0
        )

    @staticmethod
    def should_show_charges_section(run_data: Dict) -> bool:
        """Determine if charges section should be shown."""
        run_type = run_data.get("type")
        counts = RunDataParser.get_entity_counts(run_data)
        return run_type in ("charge", "all") and counts["total_charges"] > 0

    @staticmethod
    def should_show_services_section(run_data: Dict) -> bool:
        """Determine if services section should be shown."""
        run_type = run_data.get("type")
        counts = RunDataParser.get_entity_counts(run_data)
        return run_type in ("service", "all") and counts["total_services"] > 0

    @staticmethod
    def get_services_data_for_display(run_data: Dict) -> Dict:
        """Get services data for display, handling fallback scenarios."""
        run_type = run_data.get("type")
        counts = RunDataParser.get_entity_counts(run_data)

        if run_type == "service":
            # For service-only runs, use whichever bucket has data
            services = run_data.get("services_updated", {})
            if not services:
                services = run_data.get("projects_updated", {})
            return services
        else:
            return counts["services"]
