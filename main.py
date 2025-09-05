#!/usr/bin/env python3
# main.py
"""
Entry point script for Nsynca.
Updates project fields in Notion based on deployment data and task completion.
"""

import os
import argparse
from dotenv import load_dotenv
from notion_client import Client

from src.client.notion_client import NotionWrapper
from src.services.orchestrator import PageUpdaterOrchestrator, UpdaterType
from src.utils.logging import set_log_level, logger


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Update Notion database fields based on available updaters."
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )

    parser.add_argument(
        "--updaters",
        nargs="+",
        choices=["deployment", "task", "service", "all"],
        default=["all"],
        help="Which updaters to run (default: all)",
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run updaters in parallel (not implemented yet)",
    )

    return parser.parse_args()


def get_updater_types(updater_names):
    """Convert string updater names to UpdaterType enums."""
    mapping = {
        "deployment": UpdaterType.DEPLOYMENT,
        "task": UpdaterType.TASK,
        "service": UpdaterType.SERVICE,
        "all": UpdaterType.ALL,
    }
    return [mapping[name] for name in updater_names]


def main():
    """Main entry point for the application."""
    # Load environment variables from .env
    load_dotenv()

    # Parse command line arguments
    args = parse_args()

    # Set logging level
    set_log_level(args.log_level)

    # Get credentials and DB IDs from environment
    notion_token = os.getenv("NOTION_API_KEY")
    deployments_db_id = os.getenv("DEPLOYMENTS_DB_ID")
    tasks_db_id = os.getenv("TASKS_DB_ID")
    services_db_id = os.getenv("SERVICES_DB_ID")

    # Check required env vars
    if not notion_token:
        logger.error("NOTION_API_KEY environment variable not set")
        exit(1)
    if not deployments_db_id:
        logger.error("DEPLOYMENTS_DB_ID must be set in environment")
        exit(1)

    if not tasks_db_id:
        logger.error("TASKS_DB_ID must be set in environment")
        exit(1)

    if ("service" in args.updaters or "all" in args.updaters) and not services_db_id:
        logger.error("SERVICES_DB_ID must be set in environment")
        exit(1)

    try:
        # Initialize Notion client
        notion_client = Client(auth=notion_token)
        notion_wrapper = NotionWrapper(notion_client)

        # Initialize the orchestrator with configuration
        config = {
            "deployments_db_id": deployments_db_id,
            "tasks_db_id": tasks_db_id,
            "services_db_id": services_db_id,
        }

        orchestrator = PageUpdaterOrchestrator(
            notion_wrapper=notion_wrapper, config=config
        )

        # Convert updater names to types
        updater_types = get_updater_types(args.updaters)

        logger.info("Starting Notion project updates...")
        orchestrator.run(updater_types, parallel=args.parallel)
        logger.info("Project updates completed successfully!")

    except Exception as e:
        logger.error(f"Application error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
