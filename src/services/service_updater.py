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
        today = datetime.now(timezone.utc).date()
        next_due_iso: Optional[str] = None

        # Only compute next due date if service is active (not cancelled)
        if not s.end_date_at and s.last_payment_at and s.billing_cycle:
            cycle = s.billing_cycle.lower()
            last_payment_date = (
                s.last_payment_at.date()
                if isinstance(s.last_payment_at, datetime)
                else s.last_payment_at
            )

            # Calculate initial next due date
            if cycle == "monthly":
                next_due_date = last_payment_date + relativedelta(months=+1)
            elif cycle == "yearly":
                next_due_date = last_payment_date + relativedelta(years=+1)
            else:
                next_due_date = None

            # Keep adding cycles until next due date is in the future
            if next_due_date:
                while next_due_date < today:
                    if cycle == "monthly":
                        next_due_date = next_due_date + relativedelta(months=+1)
                    elif cycle == "yearly":
                        next_due_date = next_due_date + relativedelta(years=+1)

                next_due_iso = next_due_date.isoformat()

        # Determine status
        if s.end_date_at:
            status_val = "🛑 Cancelled"
        elif next_due_iso:
            next_due_date = datetime.fromisoformat(next_due_iso).date()
            if next_due_date < today:
                status_val = "🟠 Overdue"
            elif (next_due_date - today).days <= 5:
                status_val = "⏳ Coming Soon"
            else:
                status_val = "✅ Active"
        else:
            status_val = "✅ Active"

        updates = {
            "Status": {"select": {"name": status_val}},
        }

        # Handle Next Due Date
        if s.end_date_at:
            updates["Next Due Date"] = {"date": None}
        elif next_due_iso:
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
