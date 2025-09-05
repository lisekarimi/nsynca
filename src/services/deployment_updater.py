# src/services/deployment_updater.py
"""
Service for updating deployment information in Notion projects.
- Fetches all deployments once
- Groups them by project
- Processes only projects that have deployments
- Updates deployment-related fields
"""

from typing import Dict, Any, Optional, List
from .base.project_updater_base import ProjectUpdaterBase
from ..databases.deployments import (
    Deployment,
    DeploymentCollection,
    prepare_deployment_updates,
)
from ..client.notion_client import NotionWrapper
from ..utils.logging import logger


class DeploymentUpdater(ProjectUpdaterBase):
    """
    Service that updates Notion projects with deployment information.
    """

    def __init__(self, notion_wrapper: NotionWrapper, deployments_db_id: str) -> None:
        """
        Initialize the DeploymentUpdater service.

        Args:
            notion_wrapper: Wrapper for Notion API client
            deployments_db_id: ID of deployments database
        """
        super().__init__(notion_wrapper)
        self.deployments_db_id = deployments_db_id
        self._deployments_by_project: Dict[str, List[Deployment]] = {}

    def fetch_deployments(self) -> "DeploymentCollection":
        """
        Fetch all deployments from the Notion database.

        Returns:
            DeploymentCollection: Collection of deployments

        Raises:
            Exception: If deployments cannot be fetched
        """
        try:
            raw_deployments = self.notion.query_database(self.deployments_db_id)
            return DeploymentCollection(raw_deployments)
        except Exception as e:
            logger.error(f"Failed to fetch deployments: {e}")
            raise

    def _process_deployments(
        self, project_name: str, project_deployments: List[Deployment]
    ) -> Dict[str, Any]:
        """
        Process deployment data and prepare updates.

        Args:
            project_name: Name of the project for logging
            project_deployments: List of deployments for the project

        Returns:
            Dictionary of deployment updates
        """
        # Get latest deployments
        latest_dev, latest_prod = DeploymentCollection.get_latest_deployments(
            project_deployments
        )

        # Count deployments by environment
        dev_count = sum(1 for d in project_deployments if d.has_dev_deployment)
        prod_count = sum(1 for d in project_deployments if d.has_prod_deployment)

        # Log deployment info
        self._log_deployment_info(
            project_name, latest_dev, latest_prod, dev_count, prod_count
        )

        # Prepare updates
        return prepare_deployment_updates(
            latest_dev, latest_prod, dev_count, prod_count
        )

    def _log_deployment_info(
        self,
        project_name: str,
        latest_dev: Optional[Deployment],
        latest_prod: Optional[Deployment],
        dev_count: int,
        prod_count: int,
    ) -> None:
        """
        Log deployment information for debugging.

        Args:
            project_name: Name of the project
            latest_dev: Latest dev deployment or None
            latest_prod: Latest prod deployment or None
            dev_count: Number of dev deployments
            prod_count: Number of prod deployments
        """
        if latest_dev:
            logger.info(
                f"🛠 {project_name} → Last Dev: {latest_dev.version} @ {latest_dev.dev_date_string}"
            )
        else:
            logger.warning(f"🛠 {project_name} → Last Dev: none")

        if latest_prod:
            logger.info(
                f"🛠 {project_name} → Last Prod: {latest_prod.version} @ {latest_prod.prod_date_string}"
            )
        else:
            logger.warning(f"🛠 {project_name} → Last Prod: none")

        logger.info(
            f"📊 {project_name} → Dev Releases: {dev_count}, Prod Releases: {prod_count}"
        )

    def process_project(self, project_id: str) -> None:
        """
        Process a single project that has deployments.

        Args:
            project_id: ID of the project
        """
        try:
            if project_id not in self._deployments_by_project:
                logger.debug(
                    f"No deployments found for project {project_id}; skipping."
                )
                return

            # Get project info
            _, project_name = self.get_project_info(project_id)

            # Get deployments for this project - already available from run()
            deployments = self._deployments_by_project[project_id]

            # Process deployments and get updates
            updates = self._process_deployments(project_name, deployments)

            # Apply updates
            self.apply_updates(project_id, updates)

        except Exception as e:
            logger.error(f"Error processing project {project_id} for deployments: {e}")

    def run(self) -> None:
        """
        Main execution flow that updates all projects with deployment information.
        """
        try:
            logger.info("=== Starting Deployment Updates ===")

            # Step 1: Fetch all deployments
            deployment_collection = self.fetch_deployments()

            # Step 2: Group deployments by project
            self._deployments_by_project = deployment_collection.group_by_project()
            logger.info(
                f"Found deployments for {len(self._deployments_by_project)} projects"
            )

            # Step 3: Process only projects that have deployments
            for project_id in self._deployments_by_project:
                self.process_project(project_id)

            logger.info("=== Deployment Updates Complete ===")

        except Exception as e:
            logger.error(f"Deployment updater execution error: {e}")
            raise
