"""
Chuck's Hop Shop Greenwood parser.

Parses food truck schedule from Google Sheets CSV export.
Handles redirects, filters events, and processes meal categories.
"""

import csv
import io
import re
from datetime import datetime
from typing import List, Optional, Tuple

import aiohttp

from ..models import FoodTruckEvent
from ..utils.timezone_utils import (
    get_pacific_month,
    get_pacific_year,
    parse_date_with_pacific_context,
)
from .base import BaseParser


class ChucksGreenwoodParser(BaseParser):
    """Parser for Chuck's Hop Shop Greenwood food truck schedule."""

    # Month abbreviation and full name mapping to number
    MONTH_MAP = {
        "Jan": 1, "January": 1,
        "Feb": 2, "February": 2,
        "Mar": 3, "March": 3,
        "Apr": 4, "April": 4,
        "May": 5,
        "Jun": 6, "June": 6,
        "Jul": 7, "July": 7,
        "Aug": 8, "August": 8,
        "Sep": 9, "September": 9,
        "Oct": 10, "October": 10,
        "Nov": 11, "November": 11,
        "Dec": 12, "December": 12,
    }

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        """Parse food truck events from Google Sheets CSV."""
        try:
            csv_data = await self._fetch_csv(session, self.brewery.url)
            if not csv_data:
                raise ValueError("Failed to fetch CSV data")

            events = []

            # Parse CSV data
            csv_reader = csv.reader(io.StringIO(csv_data))
            rows = list(csv_reader)

            if not rows:
                self.logger.warning("CSV data is empty")
                return []

            # Skip header row if present
            data_rows = rows[1:] if len(rows) > 1 else rows

            for row_num, row in enumerate(data_rows, start=2):  # Start at 2 for header
                try:
                    event = self._parse_csv_row(row)
                    if event:
                        events.append(event)
                except Exception as e:
                    self.logger.debug(f"Error parsing row {row_num}: {row} - {str(e)}")
                    continue

            # Filter and validate events
            valid_events = self.filter_valid_events(events)
            self.logger.info(
                f"Parsed {len(valid_events)} valid events from {len(data_rows)} rows"
            )
            return valid_events

        except Exception as e:
            self.logger.error(f"Error parsing {self.brewery.name}: {str(e)}")
            raise ValueError(f"Failed to parse CSV data: {str(e)}")

    async def _fetch_csv(
        self, session: aiohttp.ClientSession, url: str
    ) -> Optional[str]:
        """Fetch CSV data from URL, handling redirects."""
        try:
            self.logger.debug(f"Fetching CSV from: {url}")

            # Allow redirects for Google Sheets → CDN
            async with session.get(url, allow_redirects=True) as response:
                if response.status == 404:
                    raise ValueError(f"CSV not found (404): {url}")
                elif response.status == 403:
                    raise ValueError(f"Access forbidden (403): {url}")
                elif response.status == 500:
                    raise ValueError(f"Server error (500): {url}")
                elif response.status != 200:
                    raise ValueError(f"HTTP {response.status}: {url}")

                content = await response.text()

                if not content or len(content.strip()) == 0:
                    raise ValueError(f"Empty CSV response from: {url}")

                # Log redirect for debugging
                if str(response.url) != url:
                    self.logger.debug(f"CSV redirected to: {response.url}")

                return content

        except aiohttp.ClientError as e:
            raise ValueError(f"Network error fetching CSV {url}: {str(e)}")
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise our custom ValueError messages
            raise ValueError(f"Failed to fetch CSV from {url}: {str(e)}")

    def _parse_csv_row(self, row: List[str]) -> Optional[FoodTruckEvent]:
        """Parse a single CSV row into a FoodTruckEvent."""
        if len(row) < 7:
            return None

        # Skip empty rows
        if not any(cell.strip() for cell in row[:7]):
            return None

        # Filter for food truck and general event rows (Column F)
        event_type_raw = row[5].strip() if len(row) > 5 else ""
        event_type_lower = event_type_raw.lower()
        
        if "event" in event_type_lower:
            event_type = "Event"
        elif "food truck" in event_type_lower:
            event_type = "Food Truck"
        elif not event_type_raw and (len(row) > 6 and row[6].strip()):
            # Fallback if column F is empty but column G has content
            event_type = "Food Truck"
        else:
            return None

        # Extract event name (Column G)
        event_name = row[6].strip() if len(row) > 6 else ""
        if not event_name or event_name == "#VALUE!":
            return None

        # Determine category
        if event_type == "Event":
            category = "trivia" if re.search(r"trivia", event_name, re.IGNORECASE) else "community"
        elif re.search(r"trivia", event_name, re.IGNORECASE):
            # Sometimes events marked as Food Truck in column F are actually trivia
            category = "trivia"
        else:
            category = "food-truck"

        # Parse vendor name and meal type from event name
        food_truck_name, meal_type = self._extract_vendor_and_meal(event_name)
        if not food_truck_name:
            self.logger.debug(f"Row failed: could not extract vendor from '{event_name}'")
            return None

        # Parse date from columns A and B (day of week and "Month Date")
        event_date = self._parse_date_from_month_date_column(row[0], row[1])
        if not event_date:
            self.logger.debug(f"Row failed: could not parse date from '{row[0]}', '{row[1]}'")
            return None

        # Set times based on meal type
        start_time, end_time = self._get_times_for_meal(event_date, meal_type)

        self.logger.debug(f"Successfully parsed: {event_date.date()} - {food_truck_name} ({category})")

        return FoodTruckEvent(
            brewery_key=self.brewery.key,
            brewery_name=self.brewery.name,
            food_truck_name=food_truck_name,
            date=event_date,
            start_time=start_time,
            end_time=end_time,
            description=meal_type.capitalize() if meal_type else None,
            category=category,
        )

    def _extract_vendor_and_meal(self, event_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract vendor name and meal type from event name."""
        if not event_name or not event_name.strip():
            return None, None

        meal_type = None
        vendor_name = event_name.strip()

        if ":" in event_name:
            parts = event_name.split(":", 1)
            if len(parts) == 2:
                prefix = parts[0].strip().lower()
                if prefix in ["brunch", "dinner"]:
                    meal_type = prefix
                    vendor_name = parts[1].strip()
        
        # Ensure we didn't end up with an empty name
        if not vendor_name:
            return None, None

        return vendor_name, meal_type

    def _get_times_for_meal(self, event_date: datetime, meal_type: Optional[str]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get start and end times based on meal type (brunch or dinner)."""
        if not meal_type:
            # Default to standard dinner hours if unknown
            return (
                event_date.replace(hour=17, minute=0, second=0, microsecond=0),
                event_date.replace(hour=21, minute=0, second=0, microsecond=0)
            )
        
        if meal_type == "brunch":
            return (
                event_date.replace(hour=11, minute=0, second=0, microsecond=0),
                event_date.replace(hour=15, minute=0, second=0, microsecond=0)
            )
        else: # dinner
            return (
                event_date.replace(hour=17, minute=0, second=0, microsecond=0),
                event_date.replace(hour=21, minute=0, second=0, microsecond=0)
            )

    def _parse_date_from_month_date_column(
        self, day_col: str, month_date_col: str
    ) -> Optional[datetime]:
        """Parse date from the combined month+date column format."""
        try:
            # Clean inputs
            month_date_str = month_date_col.strip() if month_date_col else ""

            if not month_date_str:
                return None

            # Split "Aug 1" into ["Aug", "1"]
            parts = month_date_str.split()
            if len(parts) != 2:
                self.logger.debug(f"Invalid month+date format: {month_date_str}")
                return None

            month_abbr, date_str = parts

            # Convert month abbreviation to number
            if month_abbr not in self.MONTH_MAP:
                self.logger.debug(f"Unknown month abbreviation: {month_abbr}")
                return None

            month_num = self.MONTH_MAP[month_abbr]

            # Parse day number
            try:
                day_num = int(date_str)
            except ValueError:
                self.logger.debug(f"Invalid day number: {date_str}")
                return None

            # Determine appropriate year using Pacific timezone context
            from ..utils.timezone_utils import now_in_pacific_naive
            now_pacific = now_in_pacific_naive()
            current_year = now_pacific.year
            current_month = now_pacific.month

            # Simple robust logic: 
            # 1. Start with current year
            # 2. If month is Dec and current is Jan, it's likely last year
            # 3. If month is Jan and current is Dec, it's likely next year
            # 4. Otherwise, use current year (covers most cases including end-of-month rollovers)
            
            year = current_year
            if current_month == 1 and month_num == 12:
                year = current_year - 1
            elif current_month == 12 and month_num == 1:
                year = current_year + 1

            return parse_date_with_pacific_context(year, month_num, day_num)

        except Exception as e:
            self.logger.debug(
                f"Error parsing date from {day_col}, {month_date_col}: {str(e)}"
            )
            return None
