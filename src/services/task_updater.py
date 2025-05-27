"""
Service for updating task information in Notion projects.
"""

from typing import Dict, Any, Set
from .base.project_updater_base import ProjectUpdaterBase
from ..databases.tasks import TaskCollection, prepare_task_updates
from ..utils.logging import logger


class TaskUpdater(ProjectUpdaterBase):
    """
    Service that updates Notion projects with task information.
    """

    def __init__(self, notion_wrapper, tasks_db_id: str) -> None:
        """
        Initialize the TaskUpdater service.

        Args:
            notion_wrapper: Wrapper for Notion API client
            tasks_db_id: ID of tasks database
        """
        super().__init__(notion_wrapper)
        self.tasks_db_id = tasks_db_id

    def fetch_all_tasks(self) -> TaskCollection:
        """
        Fetch all tasks from the Notion database.

        Returns:
            Collection of all tasks

        Raises:
            Exception: If tasks cannot be fetched
        """
        try:
            raw_tasks = self.notion.query_database(self.tasks_db_id)
            return TaskCollection(raw_tasks)
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {e}")
            raise

    def fetch_project_tasks(self, project_id: str) -> TaskCollection:
        """
        Fetch tasks related to a specific project.

        Args:
            project_id: ID of the project

        Returns:
            Collection of tasks

        Raises:
            Exception: If tasks cannot be fetched
        """
        try:
            filter_obj = {"property": "Project", "relation": {"contains": project_id}}
            raw_tasks = self.notion.query_database(self.tasks_db_id, filter_obj)
            return TaskCollection(raw_tasks)
        except Exception as e:
            logger.error(f"Failed to fetch tasks for project {project_id}: {e}")
            raise

    def _process_tasks(self, project_id: str, project_name: str) -> Dict[str, Any]:
        """
        Process tasks and prepare task-related updates.

        Args:
            project_id: ID of the project
            project_name: Name of the project for logging

        Returns:
            Dictionary of task-related updates
        """
        # Fetch tasks
        tasks = self.fetch_project_tasks(project_id)

        # Log task details
        logger.debug(f"Total fetched tasks for {project_name}: {tasks.total_count()}")
        for task in tasks.tasks:
            logger.debug(f" - {task.title}")

        # Log stats
        logger.info(
            f"📊 {project_name} → Total Tasks: {tasks.total_count()}, "
            f"Completed (Prod): {tasks.count_completed()}"
        )

        # Prepare updates
        return prepare_task_updates(tasks)

    def get_unique_project_ids_from_tasks(
        self, task_collection: TaskCollection
    ) -> Set[str]:
        """
        Extract unique project IDs from all tasks.

        Args:
            task_collection: Collection of tasks

        Returns:
            Set of unique project IDs
        """
        project_ids = set()
        for task in task_collection.tasks:
            # Assuming task has a project_ids property that's a list
            if hasattr(task, "project_ids") and task.project_ids:
                project_ids.update(task.project_ids)
        return project_ids

    def process_project(self, project_id: str) -> None:
        """
        Process a single project to update its task information.

        Args:
            project_id: ID of the project
        """
        try:
            # Get project info
            _, project_name = self.get_project_info(project_id)

            # Process tasks and get updates
            task_updates = self._process_tasks(project_id, project_name)

            # Apply updates
            self.apply_updates(project_id, task_updates)

        except Exception as e:
            logger.error(f"Error processing project {project_id} for tasks: {e}")

    def run(self) -> None:
        """
        Main execution flow that updates all projects with task information.
        """
        try:
            logger.info("=== Starting Task Updates ===")

            # Step 1: Fetch all tasks to get unique project IDs
            all_tasks = self.fetch_all_tasks()
            unique_project_ids = self.get_unique_project_ids_from_tasks(all_tasks)
            logger.info(f"Found tasks for {len(unique_project_ids)} projects")

            # Step 2: Process each project that has tasks
            for project_id in unique_project_ids:
                self.process_project(project_id)

            logger.info("=== Task Updates Complete ===")

        except Exception as e:
            logger.error(f"Task updater execution error: {e}")
            raise
