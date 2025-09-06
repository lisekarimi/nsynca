# src/services/charge_updater.py
"""
Updater for creating missing charge records in Notion.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from .base.page_updater_base import PageUpdaterBase
from ..databases.services import ServiceCollection, Service
from ..utils.logging import logger


class ChargeUpdater(PageUpdaterBase):
    """Create missing charge records for service profiles."""

    def __init__(self, notion_wrapper, services_db_id: str) -> None:
        """Init with Notion wrapper and DB ID."""
        super().__init__(notion_wrapper)
        self.services_db_id = services_db_id

    # def fetch_service_profiles(self) -> ServiceCollection:
    #     """Fetch service profiles with monthly or yearly billing cycles."""
    #     try:
    #         # Remove ALL filters - get everything
    #         raw = self.notion.query_database(self.services_db_id)

    #         # DEBUG: Print the raw JSON and exit
    #         import json
    #         print("=== RAW JSON RESPONSE (ALL RECORDS) ===")
    #         print(json.dumps(raw, indent=2))
    #         print(f"=== FOUND {len(raw)} TOTAL RECORDS ===")
    #         exit(1)

    #         return ServiceCollection(raw)
    #     except Exception as e:
    #         logger.error(f"Failed to fetch service profiles: {e}")
    #         raise

    def fetch_service_profiles(self) -> ServiceCollection:
        """Fetch service profiles with monthly or yearly billing cycles."""
        try:
            filter_obj = {
                "and": [
                    {"property": "Entry Type", "select": {"equals": "Service Profile"}},
                    # Remove this Name filter after testing
                    # {
                    #     "property": "Name",
                    #     "title": {"equals": "OpenAI Web"}
                    # },
                    {
                        "or": [
                            {
                                "property": "Billing Cycle",
                                "select": {"equals": "Monthly"},
                            },
                            {
                                "property": "Billing Cycle",
                                "select": {"equals": "Yearly"},
                            },
                        ]
                    },
                ]
            }
            raw = self.notion.query_database(self.services_db_id, filter_obj)
            # DEBUG: Print the raw JSON and exit
            import json

            print("=== RAW JSON RESPONSE ===")
            print(json.dumps(raw, indent=2))
            print(f"=== FOUND {len(raw)} RECORDS ===")
            # exit(1)  # Stop execution here

            return ServiceCollection(raw)
        except Exception as e:
            logger.error(f"Failed to fetch service profiles: {e}")
            raise

    def fetch_all_charges(self) -> ServiceCollection:
        """Fetch all existing charges."""
        try:
            filter_obj = {"property": "Entry Type", "select": {"equals": "Charge"}}
            raw = self.notion.query_database(self.services_db_id, filter_obj)
            return ServiceCollection(raw)
        except Exception as e:
            logger.error(f"Failed to fetch all charges: {e}")
            raise

    def get_charges_for_service(
        self, service_id: str, all_charges: List[Service]
    ) -> List[Service]:
        """Filter charges for a specific service from the full charges list."""
        return [
            charge
            for charge in all_charges
            if charge.linked_service and service_id in charge.linked_service
        ]

    def calculate_expected_charges(
        self, service: Service, existing_charges: List[Service]
    ) -> List[datetime]:
        """Calculate expected charge dates from earliest existing charge to today."""
        if not service.billing_cycle:
            return []

        # Find earliest charge date
        charges_with_dates = [c for c in existing_charges if c.date]
        if not charges_with_dates:
            raise ValueError(
                f"No existing charges found for service '{service.name}'. Cannot determine start date."
            )

        earliest_charge_date = min(charges_with_dates, key=lambda x: x.date).date

        # Calculate expected dates from earliest charge to today
        expected_dates = []
        current_date = earliest_charge_date
        today = datetime.now(timezone.utc).date()  # Convert to date object

        while current_date <= today:
            expected_dates.append(current_date)

            if service.billing_cycle.lower() == "monthly":
                current_date = current_date + relativedelta(months=1)
            elif service.billing_cycle.lower() == "yearly":
                current_date = current_date + relativedelta(years=1)
            else:
                break

        return expected_dates

    def get_charge_price(
        self, service: Service, existing_charges: List[Service]
    ) -> float:
        """Get price for new charges - from latest charge or raise error."""
        if existing_charges:
            # Sort by date and get the most recent charge price
            charges_with_dates = [c for c in existing_charges if c.date]
            if charges_with_dates:
                latest_charge = max(charges_with_dates, key=lambda x: x.date)
                if latest_charge.price is not None:
                    return latest_charge.price

        # No existing charges with price - raise error
        raise ValueError(
            f"No existing charges with price found for service '{service.name}'. Cannot determine price for new charges."
        )

    def generate_charge_name(
        self, service_name: str, charge_date: datetime.date
    ) -> str:
        """Generate charge name in format: 'ServiceName Mon25'."""
        month_abbr = charge_date.strftime("%b")  # Jan, Feb, etc.
        year_short = charge_date.strftime("%y")  # 25, 26, etc.
        return f"{service_name} {month_abbr}{year_short}"

    def create_charge_properties(
        self, service: Service, charge_date: datetime.date, price: float
    ) -> Dict[str, Any]:
        """Create properties dict for new charge record."""
        charge_name = self.generate_charge_name(service.name, charge_date)

        return {
            "Name": {"title": [{"text": {"content": charge_name}}]},
            "Entry Type": {"select": {"name": "Charge"}},
            "Date": {
                "date": {"start": charge_date.isoformat()}  # Remove .date() call
            },
            "Price": {"number": price},
            "Linked Service": {"relation": [{"id": service.id}]},
        }

    def process_service(self, service: Service, all_charges: List[Service]) -> None:
        """Process a single service and create missing charges."""
        try:
            # Get existing charges for this service
            existing_charges = self.get_charges_for_service(service.id, all_charges)
            logger.info(
                f"Found {len(existing_charges)} existing charges for {service.name}"
            )

            # Get expected charge dates
            expected_dates = self.calculate_expected_charges(service, existing_charges)
            if not expected_dates:
                logger.info(
                    f"No charges expected for {service.name} (missing billing_cycle)"
                )
                return

            logger.info(
                f"Expected {len(expected_dates)} total charges for {service.name}"
            )

            existing_dates = {
                c.date for c in existing_charges if c.date
            }  # Remove .date() call

            # Find missing charges
            missing_dates = [
                d for d in expected_dates if d not in existing_dates
            ]  # Remove .date() call

            if not missing_dates:
                logger.info(f"✅ All charges exist for {service.name}")
                return

            logger.info(
                f"Creating {len(missing_dates)} missing charges for {service.name}"
            )

            # Get price for charges
            price = self.get_charge_price(service, existing_charges)

            # Create missing charges
            for charge_date in missing_dates:
                properties = self.create_charge_properties(service, charge_date, price)
                self.notion.create_page(self.services_db_id, properties)
                charge_name = self.generate_charge_name(service.name, charge_date)
                logger.info(f"✅ Created charge: {charge_name}")

        except Exception as e:
            logger.error(f"Error processing service {service.name}: {e}")

    def process_page(self, page_id: str) -> None:
        """Process a single service page (required by base class)."""
        # This method is required by PageUpdaterBase but not used in our run() method
        # since we process services differently (with all_charges passed in)
        pass

    def run(self) -> None:
        """Main execution flow."""
        try:
            logger.info("=== Starting Charge Creation ===")

            # Fetch all data once
            service_collection = self.fetch_service_profiles()
            logger.info(f"Found {service_collection.total_count()} service profile(s)")

            if service_collection.total_count() == 0:
                logger.warning("No service profiles found matching criteria")
                return

            charges_collection = self.fetch_all_charges()
            logger.info(f"Found {charges_collection.total_count()} existing charge(s)")

            # Process each service
            for service in service_collection.services:
                logger.info(f"Processing service: {service.name}")
                self.process_service(service, charges_collection.services)

            logger.info("=== Charge Creation Complete ===")
        except Exception as e:
            logger.error(f"Charge updater execution error: {e}")
            raise
