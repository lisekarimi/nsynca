"""
Notion API client wrapper and utilities.
"""

from typing import Dict, Any, List, Optional
from notion_client import Client


class NotionWrapper:
    """
    Wrapper for Notion API client with utility methods for common operations.
    """

    def __init__(self, notion_client: Client) -> None:
        """
        Initialize Notion API client
        """
        self.client = notion_client

    def query_database(
        self, database_id: str, filter_obj: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query a Notion database with optional filters.

        Args:
            database_id: ID of the Notion database
            filter_obj: Optional filter to apply to the query

        Returns:
            List of database items

        Raises:
            Exception: If the query fails
        """
        params = {"database_id": database_id}
        if filter_obj:
            params["filter"] = filter_obj

        try:
            return self.client.databases.query(**params)["results"]
        except Exception as e:
            raise Exception(f"Failed to query database {database_id}: {e}")

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve a Notion page by ID.

        Args:
            page_id: ID of the Notion page

        Returns:
            Page object

        Raises:
            Exception: If the page retrieval fails
        """
        try:
            return self.client.pages.retrieve(page_id=page_id)
        except Exception as e:
            raise Exception(f"Failed to retrieve page {page_id}: {e}")

    def update_page(self, page_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update properties of a Notion page.

        Args:
            page_id: ID of the Notion page
            properties: Dictionary of property updates

        Returns:
            Updated page object

        Raises:
            Exception: If the update fails
        """
        try:
            return self.client.pages.update(page_id=page_id, properties=properties)
        except Exception as e:
            raise Exception(f"Failed to update page {page_id}: {e}")

    def extract_title(self, page: Dict[str, Any]) -> str:
        """
        Extract the title from a Notion page.

        Args:
            page: Notion page object

        Returns:
            Title as string or "(No title)" if not found
        """
        try:
            for prop in page["properties"].values():
                if prop["type"] == "title" and prop["title"]:
                    return prop["title"][0]["text"]["content"]
        except Exception:
            pass
        return "(No title)"
