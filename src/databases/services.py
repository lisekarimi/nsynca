# src/databases/services.py
"""
Models and utilities for working with service data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class Service:
    """
    Represents a service row from the Notion database.
    """

    def __init__(self, notion_obj: Dict[str, Any]):
        """
        Initialize a Service from a Notion object.

        Args:
            notion_obj: Raw Notion service object
        """
        self.raw = notion_obj
        self.id = notion_obj["id"]
        props = notion_obj.get("properties", {})

        self.name = _title(props.get("Name"))
        self.entry_type = _select_or_status_name(props.get("Entry Type"))
        self.billing_cycle = _select_or_status_name(props.get("Billing Cycle"))

        # Last Payment Date (rollup -> date -> start), with guards
        lp_prop = props.get("Last Payment Date") or {}
        lp_roll = lp_prop.get("rollup") or {}
        last_payment_start = (lp_roll.get("date") or {}).get("start")

        # End Date (date -> start), with guards
        end_prop = props.get("End Date") or {}
        end_date_start = (end_prop.get("date") or {}).get("start")

        self.last_payment_at = (
            datetime.fromisoformat(last_payment_start) if last_payment_start else None
        )
        self.end_date_at = (
            datetime.fromisoformat(end_date_start) if end_date_start else None
        )

        # New properties for charges and service profiles
        self.price = _number(props.get("Price"))
        self.date = _date(props.get("Date"))
        self.linked_service = _relation(props.get("Linked Service"))


class ServiceCollection:
    """
    Collection of services with utility methods.
    """

    def __init__(self, services: List[Dict[str, Any]]):
        """
        Initialize collection from raw Notion service objects.

        Args:
            services: List of raw Notion service objects
        """
        self.services = [Service(s) for s in services]

    def total_count(self) -> int:
        """Get the total number of services."""
        return len(self.services)

    def filter_by_entry_type(self, entry_type: str) -> List[Service]:
        """Filter services by entry type."""
        return [s for s in self.services if s.entry_type == entry_type]

    def charges_for_service(self, service_id: str) -> List[Service]:
        """Get all charges linked to a specific service."""
        return [
            s
            for s in self.services
            if s.entry_type == "Charge"
            and s.linked_service
            and service_id in s.linked_service
        ]


# --- Helpers ---


def _title(p) -> str:
    """Extract title text from a Notion title property."""
    try:
        if p and p.get("title"):
            return p["title"][0]["plain_text"]
    except Exception:
        pass
    return "(No title)"


def _select_or_status_name(p) -> Optional[str]:
    """Extract name from a Notion select or status property."""
    try:
        sel = p.get("select")
        if sel and sel.get("name"):
            return sel["name"]
        sts = p.get("status")
        if sts and sts.get("name"):
            return sts["name"]
    except Exception:
        pass
    return None


def _number(p) -> Optional[float]:
    """Extract number from a Notion number property."""
    try:
        if p and p.get("number") is not None:
            return float(p["number"])
    except Exception:
        pass
    return None


def _date(p) -> Optional[datetime]:
    """Extract date from a Notion date property."""
    try:
        if p and p.get("date") and p["date"].get("start"):
            return datetime.fromisoformat(p["date"]["start"]).date()
    except Exception:
        pass
    return None


def _relation(p) -> Optional[List[str]]:
    """Extract relation IDs from a Notion relation property."""
    try:
        if p and p.get("relation"):
            return [rel["id"] for rel in p["relation"]]
    except Exception:
        pass
    return None
