import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import aiohttp

from ..models import Brewery, FoodTruckEvent
from ..parsers import ParserRegistry


class ScrapingError:
    """Represents an error that occurred during scraping."""

    def __init__(
        self,
        brewery: Brewery,
        error_type: str,
        message: str,
        details: Optional[str] = None,
    ) -> None:
        self.brewery = brewery
        self.error_type = error_type
        self.message = message
        self.details = details
        self.timestamp = datetime.now()

    def __str__(self) -> str:
        return f"{self.error_type}: {self.message}"

    def to_user_message(self) -> str:
        """Create a user-facing summary of the scraping failure."""
        return f"Failed to fetch information for brewery: {self.brewery.name}"


class ScraperCoordinator:
    def __init__(
        self, max_concurrent: int = 5, timeout: int = 60, max_retries: int = 3
    ):
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        self.errors: List[ScrapingError] = []

    async def scrape_all(self, breweries: List[Brewery]) -> List[FoodTruckEvent]:
        """
        Scrape all breweries concurrently and return aggregated events.
        Returns events and stores errors for later reporting.
        """
        self.errors = []  # Reset errors for this run

        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={"User-Agent": "Around-the-Grounds Food Truck Scraper"},
        ) as session:
            tasks = []
            for brewery in breweries:
                task = self._scrape_brewery(session, brewery)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            all_events: List[FoodTruckEvent] = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # This shouldn't happen with our error handling, but just in case
                    error = ScrapingError(
                        brewery=breweries[i],
                        error_type="Unexpected Error",
                        message=f"Unexpected error: {str(result)}",
                        details=str(result),
                    )
                    self.errors.append(error)
                    self.logger.error(
                        f"Unexpected error scraping {breweries[i].name}: {result}"
                    )
                    continue

                # Type narrowing: result is Tuple[List[FoodTruckEvent], Optional[ScrapingError]]
                assert isinstance(
                    result, tuple
                ), "Result should be a tuple from _scrape_brewery"
                events: List[FoodTruckEvent]
                error_opt: Optional[ScrapingError]
                events, error_opt = result
                if error_opt:
                    self.errors.append(error_opt)
                all_events.extend(events)

        # Filter to next 7 days and sort by date
        return self._filter_and_sort_events(all_events)

    async def scrape_one(
        self, brewery: Brewery
    ) -> Tuple[List[FoodTruckEvent], Optional[ScrapingError]]:
        """Scrape a single brewery using an isolated HTTP session."""
        connector = aiohttp.TCPConnector(limit=1)
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={"User-Agent": "Around-the-Grounds Food Truck Scraper"},
        ) as session:
            events, error = await self._scrape_brewery(session, brewery)

        filtered_events = self._filter_and_sort_events(events)
        self.errors = [error] if error else []
        return filtered_events, error

    async def _scrape_brewery(
        self, session: aiohttp.ClientSession, brewery: Brewery
    ) -> Tuple[List[FoodTruckEvent], Optional[ScrapingError]]:
        """Scrape a single brewery with comprehensive error handling and retry logic."""
        try:
            parser_class = ParserRegistry.get_parser(brewery.key)
            parser = parser_class(brewery)
        except KeyError as e:
            error = ScrapingError(
                brewery=brewery,
                error_type="Configuration Error",
                message=f"Parser not found for brewery key: {brewery.key}",
                details=str(e),
            )
            self.logger.error(f"Configuration error for {brewery.name}: {str(e)}")
            return [], error

        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"Scraping {brewery.name} (attempt {attempt + 1}/{self.max_retries})..."
                )
                events = await parser.parse(session)
                # Assign brewery_url to all events
                for event in events:
                    event.brewery_url = brewery.website_url
                self.logger.info(f"Found {len(events)} events for {brewery.name}")
                return events, None

            except (asyncio.TimeoutError, aiohttp.ServerTimeoutError):
                error_msg = f"Connection timeout after {self.timeout.total}s"
                if attempt == self.max_retries - 1:
                    error = ScrapingError(
                        brewery=brewery,
                        error_type="Network Timeout",
                        message=error_msg,
                        details=f"Failed after {self.max_retries} attempts",
                    )
                    self.logger.error(f"Timeout scraping {brewery.name}: {error_msg}")
                    return [], error
                wait_time = 2**attempt  # Exponential backoff
                self.logger.warning(
                    f"Timeout scraping {brewery.name}, retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

            except aiohttp.ClientError as e:
                error_msg = f"Network error: {str(e)}"
                if attempt == self.max_retries - 1:
                    error = ScrapingError(
                        brewery=brewery,
                        error_type="Network Error",
                        message=error_msg,
                        details=f"Failed after {self.max_retries} attempts",
                    )
                    self.logger.error(
                        f"Network error scraping {brewery.name}: {error_msg}"
                    )
                    return [], error
                wait_time = 2**attempt
                self.logger.warning(
                    f"Network error scraping {brewery.name}, retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

            except ValueError as e:
                error = ScrapingError(
                    brewery=brewery,
                    error_type="Parser Error",
                    message=f"Parsing failed: {str(e)}",
                    details=str(e),
                )
                self.logger.error(f"Parser error for {brewery.name}: {str(e)}")
                return [], error

            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                if attempt == self.max_retries - 1:
                    error = ScrapingError(
                        brewery=brewery,
                        error_type="Unexpected Error",
                        message=error_msg,
                        details=str(e),
                    )
                    self.logger.error(
                        f"Unknown error scraping {brewery.name}: {error_msg}"
                    )
                    return [], error
                wait_time = 2**attempt
                self.logger.warning(
                    f"Unknown error scraping {brewery.name}, retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

        return [], None

    def _filter_and_sort_events(
        self, events: List[FoodTruckEvent]
    ) -> List[FoodTruckEvent]:
        """
        Filter events to next 7 days and sort by date.
        Uses Seattle timezone to ensure events are filtered correctly regardless of server location.
        """
        # Use Seattle timezone (PST/PDT) consistently
        seattle_tz = timezone(
            timedelta(hours=-8)
        )  # PST (PDT would be -7, but keeping simple)
        now = datetime.now(seattle_tz)
        one_week_later = now + timedelta(days=7)

        # Filter to next 7 days
        filtered_events = [
            event
            for event in events
            if now.date() <= event.date.date() <= one_week_later.date()
        ]

        # Sort by date, then by start time
        filtered_events.sort(key=lambda x: (x.date, x.start_time or x.date))

        return filtered_events

    def get_errors(self) -> List[ScrapingError]:
        """
        Get list of errors that occurred during scraping.
        """
        return self.errors

    def has_errors(self) -> bool:
        """
        Check if any errors occurred during scraping.
        """
        return len(self.errors) > 0
