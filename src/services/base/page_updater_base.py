# src/services/base/page_updater_base.py
"""
Base class for updating arbitrary Notion pages (database rows).
Provides shared functionality:
- Fetching page info
- Applying updates with error handling
- Abstract process/run lifecycle
"""

from typing import Dict, Any, Tuple
from abc import ABC, abstractmethod
from ...client.notion_client import NotionWrapper
from ...utils.logging import logger


class PageUpdaterBase(ABC):
    """
    Generic base class for updating any Notion page (row in a database).
    """

    def __init__(self, notion_wrapper: NotionWrapper) -> None:
        """
        Initialize the page updater.

        Args:
            notion_wrapper: Wrapper for Notion API client
        """
        self.notion = notion_wrapper

    def get_page_info(self, page_id: str) -> Tuple[Dict[str, Any], str]:
        """
        Get basic page information.

        Args:
            page_id: ID of the page

        Returns:
            Tuple of (page_object, page_title)
        """
        page = self.notion.get_page(page_id)
        title = self.notion.extract_title(page)
        logger.info(f"Processing page: {title}")
        return page, title

    def apply_updates(self, page_id: str, updates: Dict[str, Any]) -> None:
        """
        Apply updates to a Notion page.

        Args:
            page_id: ID of the page
            updates: Dictionary of property updates

        Raises:
            Exception: If page cannot be updated
        """
        try:
            if updates:
                self.notion.update_page(page_id, updates)
                page = self.notion.get_page(page_id)
                title = self.notion.extract_title(page)
                logger.info(f"✅ Updated page: {title}")
            else:
                logger.debug(f"No updates needed for page {page_id}")
        except Exception as e:
            logger.error(f"Failed to update page {page_id}: {e}")
            raise

    @abstractmethod
    def process_page(self, page_id: str) -> None:
        """
        Process a single page.
        Must be implemented by subclasses.

        Args:
            page_id: ID of the page to process
        """
        pass

    @abstractmethod
    def run(self) -> None:
        """
        Main execution flow.
        Must be implemented by subclasses.
        """
        pass
