from datetime import datetime, timedelta
from typing import List, Optional

import aiohttp

from ..models import Brewery, FoodTruckEvent
from ..utils.timezone_utils import now_in_pacific_naive
from .base import BaseParser


class BarkingDogParser(BaseParser):
    """
    Static parser for The Barking Dog Alehouse.
    Since the site is protected by Cloudflare and events are largely recurring,
    we use a static schedule for now.
    """

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        events: List[FoodTruckEvent] = []
        now = now_in_pacific_naive()
        
        # Generate recurring events for the next 14 days to ensure coverage
        for i in range(14):
            current_date = now + timedelta(days=i)
            weekday = current_date.weekday() # 0 is Monday, 1 is Tuesday, etc.
            
            # Tuesday: Trivia Night
            if weekday == 1:
                events.append(
                    FoodTruckEvent(
                        brewery_key=self.brewery.key,
                        brewery_name=self.brewery.name,
                        food_truck_name="Trivia Night",
                        date=current_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        start_time=current_date.replace(hour=19, minute=0, second=0, microsecond=0),
                        end_time=current_date.replace(hour=21, minute=0, second=0, microsecond=0),
                        description="Trivia",
                        category="trivia"
                    )
                )
            
            # Wednesday: Wine Wednesday
            if weekday == 2:
                events.append(
                    FoodTruckEvent(
                        brewery_key=self.brewery.key,
                        brewery_name=self.brewery.name,
                        food_truck_name="Wine Wednesday",
                        date=current_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        description="All bottles of wine are half off all day long.",
                        category="community"
                    )
                )
                
        return events
