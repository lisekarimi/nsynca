"""
Models and utilities for working with deployment data.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class Deployment:
    """
    Represents a deployment with dev and prod information.
    """

    def __init__(self, notion_obj: Dict[str, Any]):
        """
        Initialize a Deployment from a Notion object.

        Args:
            notion_obj: Raw Notion deployment object
        """
        self.raw_data = notion_obj
        self.project_id = self._extract_project_id()
        self.version = self._extract_version()

        # Extract and parse dates
        dev_date = notion_obj["properties"].get("Dev Deployed Date", {}).get("date")
        prod_date = notion_obj["properties"].get("Prod Deployed Date", {}).get("date")

        self.dev_date = datetime.fromisoformat(dev_date["start"]) if dev_date else None
        self.prod_date = (
            datetime.fromisoformat(prod_date["start"]) if prod_date else None
        )

    def _extract_project_id(self) -> Optional[str]:
        """
        Extract project ID from the deployment.

        Returns:
            Project ID or None if not found
        """
        try:
            relations = self.raw_data["properties"]["Project"]["relation"]
            if relations:
                return relations[0]["id"]
        except (KeyError, IndexError):
            pass
        return None

    def _extract_version(self) -> str:
        """
        Extract version string from the deployment.

        Returns:
            Version string or empty string if not found
        """
        try:
            version = self.raw_data["properties"]["Version"]["title"]
            if version:
                return version[0]["text"]["content"]
        except (KeyError, IndexError):
            pass
        return ""

    @property
    def has_dev_deployment(self) -> bool:
        """Check if this deployment has dev date information."""
        return self.dev_date is not None

    @property
    def has_prod_deployment(self) -> bool:
        """Check if this deployment has prod date information."""
        return self.prod_date is not None

    @property
    def dev_date_string(self) -> Optional[str]:
        """Get the dev date as ISO string or None."""
        try:
            return self.raw_data["properties"]["Dev Deployed Date"]["date"]["start"]
        except (KeyError, TypeError):
            return None

    @property
    def prod_date_string(self) -> Optional[str]:
        """Get the prod date as ISO string or None."""
        try:
            return self.raw_data["properties"]["Prod Deployed Date"]["date"]["start"]
        except (KeyError, TypeError):
            return None


class DeploymentCollection:
    """
    Collection of deployments with utility methods.
    """

    def __init__(self, deployments: List[Dict[str, Any]]):
        """
        Initialize collection from raw Notion deployment objects.

        Args:
            deployments: List of raw Notion deployment objects
        """
        self.deployments = [Deployment(d) for d in deployments]

    def group_by_project(self) -> Dict[str, List[Deployment]]:
        """
        Group deployments by project ID.

        Returns:
            Dictionary mapping project IDs to lists of deployments.
            Only includes projects that have at least one deployment.
        """
        result = defaultdict(list)
        for deployment in self.deployments:
            if deployment.project_id:
                result[deployment.project_id].append(deployment)
        return result

    @staticmethod
    def get_latest_deployments(
        project_deployments: List[Deployment],
    ) -> Tuple[Optional[Deployment], Optional[Deployment]]:
        """
        Find the latest dev and prod deployments from a list.

        Args:
            project_deployments: List of deployments for a project

        Returns:
            Tuple of (latest_dev_deployment, latest_prod_deployment)
        """
        # Filter deployments by environment
        dev_deployments = [d for d in project_deployments if d.has_dev_deployment]
        prod_deployments = [d for d in project_deployments if d.has_prod_deployment]

        # Get latest by date
        latest_dev = (
            max(dev_deployments, key=lambda d: d.dev_date) if dev_deployments else None
        )
        latest_prod = (
            max(prod_deployments, key=lambda d: d.prod_date)
            if prod_deployments
            else None
        )

        return latest_dev, latest_prod


def prepare_deployment_updates(
    latest_dev: Optional[Deployment],
    latest_prod: Optional[Deployment],
    dev_count: int,
    prod_count: int,
) -> Dict[str, Any]:
    """
    Prepare Notion property updates based on deployment data.

    Args:
        latest_dev: Latest dev deployment or None
        latest_prod: Latest prod deployment or None
        dev_count: Number of dev deployments
        prod_count: Number of prod deployments

    Returns:
        Dictionary of Notion property updates
    """
    updates = {}

    # Last Dev info
    if latest_dev and latest_dev.dev_date_string:
        updates["Last Dev Deploy"] = {"date": {"start": latest_dev.dev_date_string}}
        updates["Last Dev Version"] = {
            "rich_text": [{"type": "text", "text": {"content": latest_dev.version}}]
        }

    # Last Prod info
    if latest_prod and latest_prod.prod_date_string:
        updates["Last Prod Deploy"] = {"date": {"start": latest_prod.prod_date_string}}
        updates["Last Prod Version"] = {
            "rich_text": [{"type": "text", "text": {"content": latest_prod.version}}]
        }

    # Add release counters
    updates["Nb Dev Releases"] = {"number": dev_count}
    updates["Nb Prod Releases"] = {"number": prod_count}

    return updates
