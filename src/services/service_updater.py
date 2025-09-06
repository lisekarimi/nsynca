# src/services/service_updater.py
"""
Updater for service rows in Notion.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from .base.page_updater_base import PageUpdaterBase
from ..databases.services import ServiceCollection, Service
from ..utils.logging import logger


class ServiceUpdater(PageUpdaterBase):
    """Update service rows in the Services DB."""

    def __init__(self, notion_wrapper, services_db_id: str) -> None:
        """Init with Notion wrapper and DB ID."""
        super().__init__(notion_wrapper)
        self.services_db_id = services_db_id

    def fetch_services(self) -> "ServiceCollection":
        """Fetch only 'Service Profile' rows from the DB."""
        try:
            filter_obj = {
                "property": "Entry Type",
                "select": {"equals": "Service Profile"},
            }
            raw = self.notion.query_database(self.services_db_id, filter_obj)
            return ServiceCollection(raw)
        except Exception as e:
            logger.error(f"Failed to fetch services: {e}")
            raise

    def _compute_updates(self, s: Service) -> Dict[str, Any]:
        """Compute property updates for a service."""
        # Update Next Due Date
        next_due_iso: Optional[str] = (
            None  # store Next Due Date as ISO string for Notion
        )
        if (
            s.last_payment_at and s.billing_cycle
        ):  # only compute if we have payment + cycle
            cycle = s.billing_cycle.lower()  # normalize for comparison
            if cycle == "monthly":
                next_due_iso = (
                    (s.last_payment_at + relativedelta(months=+1)).date().isoformat()
                )  # add 1 month
            elif cycle == "annual":
                next_due_iso = (
                    (s.last_payment_at + relativedelta(years=+1)).date().isoformat()
                )  # add 1 year

        # Update Status
        today = datetime.now(timezone.utc).date()
        if s.end_date_at:
            status_val = "Cancelled"
        elif next_due_iso:
            next_due_date = datetime.fromisoformat(next_due_iso).date()
            if next_due_date < today:
                status_val = "Overdue"
            elif (next_due_date - today).days <= 5:
                status_val = "Coming Soon"
            else:
                status_val = "Active"
        else:
            status_val = "Active"

        updates = {
            "Status": {"select": {"name": status_val}},
        }
        # Only add Next Due Date if we have a valid date
        if next_due_iso:
            updates["Next Due Date"] = {"date": {"start": next_due_iso}}

        return updates

    def process_page(self, page_id: str) -> None:
        """Process and update a single service row."""
        try:
            page, title = self.get_page_info(page_id)
            s = Service(page)
            updates = self._compute_updates(s)
            self.apply_updates(page_id, updates)
            logger.info(f"✅ Updated service: {title}")
        except Exception as e:
            logger.error(f"Error processing service {page_id}: {e}")

    def run(self) -> None:
        """Main execution flow.
        Fetch all services and update each row.
        """
        try:
            logger.info("=== Starting Service Updates ===")
            collection = self.fetch_services()
            for s in collection.services:
                self.process_page(s.id)
            logger.info("=== Service Updates Complete ===")
        except Exception as e:
            logger.error(f"Service updater execution error: {e}")
            raise
