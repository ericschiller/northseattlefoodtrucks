import re
from datetime import datetime, timedelta
from typing import List, Optional

import aiohttp

from ..models import Brewery, FoodTruckEvent
from ..utils.timezone_utils import now_in_pacific_naive
from .google_calendar import GoogleCalendarParser


class WatershedParser(GoogleCalendarParser):
    """
    Parser for Watershed Pub & Kitchen.
    Combines public iCal feed with static recurring events not in the feed.
    """

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        # 1. Get events from the base GoogleCalendarParser (iCal feed)
        ical_events = await super().parse(session)
        
        # 2. Add static recurring events that are on their website but missing from iCal
        recurring_events: List[FoodTruckEvent] = []
        now = now_in_pacific_naive()
        
        for i in range(14):
            current_date = now + timedelta(days=i)
            weekday = current_date.weekday() # 0 is Monday, 1 is Tuesday
            
            # Monday: Music Mondays
            if weekday == 0:
                recurring_events.append(
                    FoodTruckEvent(
                        brewery_key=self.brewery.key,
                        brewery_name=self.brewery.name,
                        food_truck_name="Music Mondays",
                        date=current_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        start_time=current_date.replace(hour=20, minute=0, second=0, microsecond=0),
                        end_time=current_date.replace(hour=23, minute=59, second=0, microsecond=0),
                        description="Music videos and pizza by the slice.",
                        category="community"
                    )
                )
            
            # Tuesday: Stump Trivia
            if weekday == 1:
                # Two sessions: 7pm and 8pm
                recurring_events.append(
                    FoodTruckEvent(
                        brewery_key=self.brewery.key,
                        brewery_name=self.brewery.name,
                        food_truck_name="Stump Trivia",
                        date=current_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        start_time=current_date.replace(hour=19, minute=0, second=0, microsecond=0),
                        end_time=current_date.replace(hour=21, minute=0, second=0, microsecond=0),
                        description="Fun, free trivia with prizes! Two sessions at 7pm and 8pm.",
                        category="trivia"
                    )
                )
                
        # Merge and deduplicate
        all_events = ical_events + recurring_events
        return self._dedupe_final(all_events)

    def _dedupe_final(self, events: List[FoodTruckEvent]) -> List[FoodTruckEvent]:
        seen = set()
        deduped = []
        for event in events:
            # Key by date and name (case-insensitive)
            key = (event.date.date(), event.food_truck_name.lower())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(event)
        return deduped
