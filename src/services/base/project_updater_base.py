# src/services/base/project_updater_base.py
"""
Specialized base class for updating project pages in Notion.
Builds on PageUpdaterBase but keeps project-specific method names
for backward compatibility.
"""

from abc import abstractmethod
from .page_updater_base import PageUpdaterBase


class ProjectUpdaterBase(PageUpdaterBase):
    """
    Project-specific updater base that preserves legacy naming.
    """

    def get_project_info(self, project_id: str):
        """
        Get project information.

        Args:
            project_id: ID of the project

        Returns:
            Tuple of (project_object, project_name)
        """
        return super().get_page_info(project_id)

    def apply_updates(self, project_id: str, updates):
        """
        Apply updates to a project.

        Args:
            project_id: ID of the project
            updates: Dictionary of property updates
        """
        return super().apply_updates(project_id, updates)

    @abstractmethod
    def process_project(self, project_id: str) -> None:
        """
        Abstract method for subclasses to implement project-specific processing.

        Args:
            project_id: ID of the project to process
        """
        ...

    def process_page(self, page_id: str) -> None:
        """
        Adapter method to satisfy PageUpdaterBase’s abstract interface.
        Delegates to process_project for backward compatibility.
        """
        self.process_project(page_id)
