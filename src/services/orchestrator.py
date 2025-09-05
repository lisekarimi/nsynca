# src/services/orchestrator.py
"""
Orchestrator for coordinating multiple page updaters (projects, tasks, services).
"""

from typing import List, Optional, Dict
from enum import Enum
from ..client.notion_client import NotionWrapper
from .deployment_updater import DeploymentUpdater
from .task_updater import TaskUpdater
from .service_updater import ServiceUpdater
from ..utils.logging import logger


class UpdaterType(Enum):
    """
    Types of available updaters.
    """

    DEPLOYMENT = "deployment"
    TASK = "task"
    SERVICE = "service"
    ALL = "all"


class PageUpdaterOrchestrator:
    """
    Orchestrates the execution of multiple page updaters (project- and service-level).
    """

    def __init__(self, notion_wrapper: NotionWrapper, config: Dict[str, str]) -> None:
        """
        Initialize the orchestrator with necessary configuration.

        Args:
            notion_wrapper: Wrapper for Notion API client
            config: Dictionary containing database IDs
        """
        self.notion = notion_wrapper
        self.config = config

        # Initialize updaters
        self.deployment_updater = DeploymentUpdater(
            notion_wrapper, config["deployments_db_id"]
        )
        self.task_updater = TaskUpdater(notion_wrapper, config["tasks_db_id"])
        self.service_updater = ServiceUpdater(notion_wrapper, config["services_db_id"])

        # Map updater types to instances
        self.updaters = {
            UpdaterType.DEPLOYMENT: self.deployment_updater,
            UpdaterType.TASK: self.task_updater,
            UpdaterType.SERVICE: self.service_updater,
        }

    def run(
        self, updater_types: Optional[List[UpdaterType]] = None, parallel: bool = False
    ) -> None:
        """
        Run specified updaters.

        Args:
            updater_types: List of updater types to run. If None, runs all.
            parallel: Whether to run updaters in parallel (not implemented yet)
        """
        try:
            logger.info("=== Starting Page Update Orchestration ===")

            # Determine which updaters to run
            if updater_types is None or UpdaterType.ALL in updater_types:
                updaters_to_run = list(self.updaters.values())
                logger.info("Running all updaters")
            else:
                updaters_to_run = [
                    self.updaters[ut] for ut in updater_types if ut in self.updaters
                ]
                logger.info(f"Running updaters: {[ut.value for ut in updater_types]}")

            # Execute updaters
            if parallel:
                # TODO: Implement parallel execution using threading or async
                logger.warning(
                    "Parallel execution not implemented yet. Running sequentially."
                )
                self._run_sequential(updaters_to_run)
            else:
                self._run_sequential(updaters_to_run)

            logger.info("=== Page Update Orchestration Complete ===")

        except Exception as e:
            logger.error(f"Orchestrator execution error: {e}")
            raise

    def _run_sequential(self, updaters: List) -> None:
        """
        Run updaters sequentially.

        Args:
            updaters: List of updater instances to run
        """
        for updater in updaters:
            try:
                updater.run()
            except Exception as e:
                logger.error(f"Error running {updater.__class__.__name__}: {e}")
                # Continue with other updaters even if one fails
                continue

    def run_deployment_updates(self) -> None:
        """
        Convenience method to run only deployment updates.
        """
        self.run([UpdaterType.DEPLOYMENT])

    def run_task_updates(self) -> None:
        """
        Convenience method to run only task updates.
        """
        self.run([UpdaterType.TASK])

    def run_service_updates(self) -> None:
        """
        Convenience method to run only service updates.
        """
        self.run([UpdaterType.SERVICE])

    def run_all_updates(self) -> None:
        """
        Convenience method to run all updates.
        """
        self.run([UpdaterType.ALL])


def create_orchestrator(
    notion_token: str, deployments_db_id: str, tasks_db_id: str, services_db_id: str
) -> PageUpdaterOrchestrator:
    """
    Factory function to create an orchestrator instance.

    Args:
        notion_token: Notion API token

    Returns:
        Configured PageUpdaterOrchestrator instance
    """
    notion_wrapper = NotionWrapper(notion_token)
    config = {
        "deployments_db_id": deployments_db_id,
        "tasks_db_id": tasks_db_id,
        "services_db_id": services_db_id,
    }
    return PageUpdaterOrchestrator(notion_wrapper, config)
