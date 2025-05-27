"""
Base class for project updaters with shared functionality:
- Getting project info
- Applying updates to Notion
- Abstract methods for subclasses to implement
"""

from typing import Dict, Any, Tuple
from abc import ABC, abstractmethod
from ...client.notion_client import NotionWrapper
from ...utils.logging import logger


class ProjectUpdaterBase(ABC):
    """
    Base class for all project updaters providing common functionality.
    """

    def __init__(self, notion_wrapper: NotionWrapper) -> None:
        """
        Initialize the base updater.

        Args:
            notion_wrapper: Wrapper for Notion API client
        """
        self.notion = notion_wrapper

    def get_project_info(self, project_id: str) -> Tuple[Dict[str, Any], str]:
        """
        Get basic project information.

        Args:
            project_id: ID of the project

        Returns:
            Tuple of (project_object, project_name)
        """
        project = self.notion.get_page(project_id)
        project_name = self.notion.extract_title(project)
        logger.info(f"Processing project: {project_name}")
        return project, project_name

    def apply_updates(self, project_id: str, updates: Dict[str, Any]) -> None:
        """
        Apply updates to a project.

        Args:
            project_id: ID of the project
            updates: Dictionary of property updates

        Raises:
            Exception: If project cannot be updated
        """
        try:
            if updates:
                self.notion.update_page(project_id, updates)
                project = self.notion.get_page(project_id)
                project_name = self.notion.extract_title(project)
                logger.info(f"✅ Updated project: {project_name}")
            else:
                logger.debug(f"No updates needed for project {project_id}")
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            raise

    @abstractmethod
    def process_project(self, project_id: str) -> None:
        """
        Process a single project. Must be implemented by subclasses.

        Args:
            project_id: ID of the project to process
        """
        pass

    @abstractmethod
    def run(self) -> None:
        """
        Main execution flow. Must be implemented by subclasses.
        """
        pass
