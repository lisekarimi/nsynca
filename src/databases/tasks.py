"""
Models and utilities for working with task data.
"""

from typing import Dict, Any, List, Optional


class Task:
    """
    Represents a task from the Notion database.
    """

    # Status that marks a task as completed
    COMPLETED_STATUS = "Prod Deployed"
    STATUS_PROPERTY_KEY = "Status "

    def __init__(self, notion_obj: Dict[str, Any]):
        """
        Initialize a Task from a Notion object.

        Args:
            notion_obj: Raw Notion task object
        """
        self.raw_data = notion_obj
        self.title = self._extract_title()
        self.status = self._extract_status()
        self.project_ids = self._extract_project_ids()

    def _extract_title(self) -> str:
        """
        Extract the title from the task.

        Returns:
            Title string or "(No title)" if not found
        """
        try:
            for prop in self.raw_data["properties"].values():
                if prop["type"] == "title" and prop["title"]:
                    return prop["title"][0]["text"]["content"]
        except (KeyError, IndexError):
            pass
        return "(No title)"

    def _extract_status(self) -> Optional[str]:
        """
        Extract the status from the task.

        Returns:
            Status string or None if not found
        """
        try:
            status_prop = self.raw_data["properties"][self.STATUS_PROPERTY_KEY]
            if status_prop.get("select"):
                return status_prop["select"]["name"]
        except KeyError:
            pass
        return None

    def _extract_project_ids(self) -> List[str]:
        """
        Extract project IDs related to this task.

        Returns:
            List of project IDs
        """
        try:
            relations = self.raw_data["properties"]["Project"]["relation"]
            return [relation["id"] for relation in relations]
        except KeyError:
            return []

    @property
    def is_completed(self) -> bool:
        """
        Check if the task is completed (has 'Prod Deployed' status).

        Returns:
            True if the task is completed, False otherwise
        """
        return self.status == self.COMPLETED_STATUS


class TaskCollection:
    """
    Collection of tasks with utility methods.
    """

    def __init__(self, tasks: List[Dict[str, Any]]):
        """
        Initialize collection from raw Notion task objects.

        Args:
            tasks: List of raw Notion task objects
        """
        self.tasks = [Task(t) for t in tasks]

    def count_completed(self) -> int:
        """
        Count the number of completed tasks in the collection.

        Returns:
            Number of completed tasks
        """
        return sum(1 for task in self.tasks if task.is_completed)

    def total_count(self) -> int:
        """
        Get the total number of tasks in the collection.

        Returns:
            Total number of tasks
        """
        return len(self.tasks)

    def filter_by_project(self, project_id: str) -> "TaskCollection":
        """
        Filter tasks by project ID.

        Args:
            project_id: Project ID to filter by

        Returns:
            New TaskCollection with filtered tasks
        """
        filtered_tasks = [t.raw_data for t in self.tasks if project_id in t.project_ids]
        return TaskCollection(filtered_tasks)


def prepare_task_updates(tasks: TaskCollection) -> Dict[str, Any]:
    """
    Prepare Notion property updates based on task statistics.

    Args:
        tasks: Collection of tasks

    Returns:
        Dictionary of Notion property updates
    """
    return {
        "Total Tasks": {"number": tasks.total_count()},
        "Completed Tasks": {"number": tasks.count_completed()},
    }
