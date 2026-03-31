import json
import re
from datetime import datetime, timezone
from typing import Any, List, Optional

import aiohttp

try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

from ..models import Brewery, FoodTruckEvent
from .base import BaseParser


class SquarespaceEventsParser(BaseParser):
    """
    Generic parser for Squarespace events/calendar pages.
    Can fetch data via ?format=json or via the GetItemsByMonth API.
    """

    def __init__(self, brewery: Brewery) -> None:
        super().__init__(brewery)
        self.exclude_patterns = self.brewery.parser_config.get("exclude_patterns", [])
        self.category_patterns: dict = self.brewery.parser_config.get("category_patterns", {})

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        try:
            # Try fetching with ?format=json first as it's the most direct for "Events" collections
            json_url = self.brewery.url
            if "?" in json_url:
                json_url += "&format=json"
            else:
                json_url += "?format=json"

            self.logger.debug(f"Fetching Squarespace JSON from: {json_url}")
            async with session.get(json_url) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get("items", [])
                    if items:
                        events = []
                        for item in items:
                            title = item.get("title", "").strip()
                            category = self._get_category(title)
                            if category is None:
                                continue
                            event = self._parse_json_item(item, category)
                            if event:
                                events.append(event)
                        
                        valid_events = self.filter_valid_events(events)
                        self.logger.info(f"Parsed {len(valid_events)} valid events from {len(items)} items")
                        return valid_events

            # Fallback to collection-based API if ?format=json didn't work or returned no items
            # (Similar to Bale Breaker logic)
            return await self._parse_via_collection_api(session)

        except Exception as e:
            self.logger.error(f"Error parsing Squarespace events for {self.brewery.key}: {str(e)}")
            return []

    async def _parse_via_collection_api(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        # Implementation similar to BaleBreakerParser for robustness
        collection_id = None
        try:
            soup = await self.fetch_page(session, self.brewery.url)
            if soup:
                collection_id = self._extract_collection_id(soup)
        except Exception as e:
            self.logger.error(f"Error fetching main page for {self.brewery.key}: {str(e)}")

        if not collection_id:
            return []

        events = []
        try:
            from datetime import timedelta
            now = datetime.now()
            # Get current month and next month
            months_to_fetch = [
                (now.year, now.month),
                ((now + timedelta(days=32)).year, (now + timedelta(days=32)).month),
            ]

            month_names = ["January", "February", "March", "April", "May", "June", 
                           "July", "August", "September", "October", "November", "December"]

            # Try both possible API endpoints
            # 1. api/open/GetItemsByMonth (used by Bale Breaker)
            # 2. api/content/v1/GetItemsByMonth (modern version)
            
            # Extract domain from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(self.brewery.url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            for year, month in months_to_fetch:
                month_str = f"{month_names[month - 1]}-{year}"
                
                # We'll try the /api/open endpoint first
                api_url = f"{base_url}/api/open/GetItemsByMonth?month={month_str}&collectionId={collection_id}"
                self.logger.debug(f"Fetching calendar data from: {api_url}")

                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data:
                            title = item.get("title", "").strip()
                            category = self._get_category(title)
                            if category is None:
                                continue
                            event = self._parse_json_item(item, category)
                            if event:
                                events.append(event)
                    else:
                        self.logger.warning(f"API request failed with status {response.status} for {api_url}")

            return self.filter_valid_events(events)
        except Exception as e:
            self.logger.error(f"Error in _parse_via_collection_api for {self.brewery.key}: {str(e)}")
            return []

    def _extract_collection_id(self, soup: Any) -> Optional[str]:
        """Extract the Squarespace calendar collection ID from the page"""
        try:
            # Look for calendar block with data-block-json attribute
            calendar_blocks = soup.find_all("div", {"class": "calendar-block"})
            for block in calendar_blocks:
                data_json = block.get("data-block-json")
                if data_json:
                    import html
                    decoded_json = html.unescape(data_json)
                    block_data = json.loads(decoded_json)
                    collection_id = block_data.get("collectionId")
                    if collection_id:
                        return str(collection_id)

            # Fallback: look in script tags for collection info
            scripts = soup.find_all("script")
            for script in scripts:
                if not script.string:
                    continue
                
                text = script.string
                
                # Try common patterns in SQUARESPACE_CONTEXT or other scripts
                patterns = [
                    r'"collectionId"\s*:\s*"([^"]+)"',
                    r'"collection"\s*:\s*\{[^}]*"id"\s*:\s*"([^"]+)"',
                    r'collectionId\s*=\s*"([^"]+)"',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        return match.group(1)
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting collection ID: {str(e)}")
            return None

    def _parse_json_item(self, item: dict, category: str = "food-truck") -> Optional[FoodTruckEvent]:
        try:
            title = item.get("title", "").strip()
            if not title:
                return None

            # Squarespace timestamps are in milliseconds
            start_ts = item.get("startDate")
            end_ts = item.get("endDate")

            if not start_ts:
                return None

            # Use proper Pacific timezone
            pacific_tz = ZoneInfo("America/Los_Angeles")
            
            start_date_utc = datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc)
            start_date_pacific = start_date_utc.astimezone(pacific_tz)
            start_date = start_date_pacific.replace(tzinfo=None)

            end_date = None
            if end_ts:
                end_date_utc = datetime.fromtimestamp(end_ts / 1000, tz=timezone.utc)
                end_date_pacific = end_date_utc.astimezone(pacific_tz)
                end_date = end_date_pacific.replace(tzinfo=None)

            return FoodTruckEvent(
                brewery_key=self.brewery.key,
                brewery_name=self.brewery.name,
                food_truck_name=title,
                date=start_date,
                start_time=start_date,
                end_time=end_date,
                description=None,
                category=category,
            )
        except Exception as e:
            self.logger.error(f"Error parsing Squarespace JSON item: {str(e)}")
            return None

    def _get_category(self, title: str) -> Optional[str]:
        """Return the event category, or None to exclude the event.

        - None: hard-exclude (header entries, meta items)
        - "food-truck": it's a food truck booking
        - "trivia", "community", etc.: a non-truck event to include in Events tab
        """
        for pattern in self.exclude_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return None
        for pattern, category in self.category_patterns.items():
            if re.search(pattern, title, re.IGNORECASE):
                return category
        return "food-truck"
