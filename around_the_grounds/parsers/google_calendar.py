"""Google Calendar iCal parser for public calendar feeds."""

import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import aiohttp

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

from ..models import Brewery, FoodTruckEvent
from .base import BaseParser

_PACIFIC = ZoneInfo("America/Los_Angeles")
_WEEKDAY = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}

_CATEGORY_RULES: List[Tuple[str, str]] = [
    (r"live\s*music|concert|open\s*mic|jam\s*session|jazz", "live-music"),
    (r"trivia", "trivia"),
    (r"run(ning)?\s*club", "community"),
    (r"yarnaholics|knitting|choir", "community"),
    (r"food\s*truck", "food-truck"),
]


def _clean_summary(summary: str) -> str:
    """Remove common prefixes from event summary."""
    # Remove "Dinner:", "Brunch:", "Food Truck:", etc.
    cleaned = re.sub(r"^(dinner|brunch|food\s*truck|event)\s*:\s*", "", summary, flags=re.IGNORECASE)
    return cleaned.strip()


def _categorize(summary: str) -> str:
    for pattern, cat in _CATEGORY_RULES:
        if re.search(pattern, summary, re.IGNORECASE):
            return cat
    return "community"


def _parse_dt(params: str, value: str) -> Optional[datetime]:
    """Parse an iCal property value into a Pacific-naive datetime."""
    params_upper = params.upper()
    try:
        if "VALUE=DATE" in params_upper:
            return datetime.strptime(value, "%Y%m%d")
        elif value.endswith("Z"):
            dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ")
            return dt.replace(tzinfo=timezone.utc).astimezone(_PACIFIC).replace(tzinfo=None)
        else:
            return datetime.strptime(value, "%Y%m%dT%H%M%S")
    except ValueError:
        return None


def _midnight(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _parse_rrule(rrule_value: str) -> Tuple[Optional[str], Optional[datetime]]:
    """Return (byday, until) for a FREQ=WEEKLY rule, else (None, None)."""
    if "FREQ=WEEKLY" not in rrule_value.upper():
        return None, None

    byday_m = re.search(r"BYDAY=([A-Z,]+)", rrule_value, re.IGNORECASE)
    byday = byday_m.group(1).upper() if byday_m else None

    until: Optional[datetime] = None
    until_m = re.search(r"UNTIL=(\d{8}T\d{6}Z)", rrule_value, re.IGNORECASE)
    if until_m:
        try:
            until = (
                datetime.strptime(until_m.group(1), "%Y%m%dT%H%M%SZ")
                .replace(tzinfo=timezone.utc)
                .astimezone(_PACIFIC)
                .replace(tzinfo=None)
            )
        except ValueError:
            pass

    return byday, until


def _expand_weekly(
    dtstart: datetime,
    dtend: Optional[datetime],
    byday: str,
    until: Optional[datetime],
    window: int = 14,
) -> List[Tuple[datetime, Optional[datetime]]]:
    """Expand a weekly recurring rule into concrete (start, end) pairs within `window` days."""
    target_days = {
        _WEEKDAY[d.strip()] for d in byday.split(",") if d.strip() in _WEEKDAY
    }
    if not target_days:
        return []

    now = datetime.now(tz=_PACIFIC).replace(tzinfo=None)
    cutoff = now + timedelta(days=window)
    duration = (dtend - dtstart) if dtend else None

    results = []
    cursor = _midnight(dtstart)  # Start from the event's original start date
    while cursor <= cutoff:
        if cursor.weekday() in target_days:
            occ_start = cursor.replace(
                hour=dtstart.hour, minute=dtstart.minute, second=0, microsecond=0
            )
            # Only include if it's within our window (today onwards)
            if occ_start.date() >= now.date() and (until is None or occ_start <= until):
                occ_end = occ_start + duration if duration else None
                results.append((occ_start, occ_end))
        cursor += timedelta(days=1)
    return results


class GoogleCalendarParser(BaseParser):
    """Parser for public Google Calendar iCal feeds."""

    async def parse(self, session: aiohttp.ClientSession) -> List[FoodTruckEvent]:
        try:
            async with session.get(self.brewery.url) as response:
                if response.status != 200:
                    self.logger.error(
                        f"HTTP {response.status} fetching iCal from {self.brewery.url}"
                    )
                    return []
                text = await response.text()
            events = self._parse_ical(text)
            valid = self.filter_valid_events(events)
            self.logger.info(
                f"Parsed {len(valid)} events from Google Calendar for {self.brewery.key}"
            )
            return valid
        except Exception as e:
            self.logger.error(
                f"Error parsing Google Calendar for {self.brewery.key}: {e}"
            )
            return []

    def _parse_ical(self, text: str) -> List[FoodTruckEvent]:
        unfolded = re.sub(r"\r?\n[ \t]", "", text)
        blocks = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", unfolded, re.DOTALL)
        
        # We'll store events along with a "specificity" score
        # 2 = Specific override (has RECURRENCE-ID)
        # 1 = Single event (no RRULE)
        # 0 = Generated from a recurring series
        all_parsed: List[Tuple[FoodTruckEvent, int]] = []
        
        for block in blocks:
            # We need to know if it was recurring to score it
            is_recurring = "RRULE:" in block.upper()
            has_recurrence_id = "RECURRENCE-ID" in block.upper()
            
            score = 0
            if has_recurrence_id:
                score = 2
            elif not is_recurring:
                score = 1
                
            events = self._parse_vevent(block)
            for e in events:
                all_parsed.append((e, score))
        
        # Deduplicate by slot (date, start_time), keeping the one with the highest score
        # If scores are tied, we take the one that appeared later in the file (often the update)
        best_events: Dict[Tuple, Tuple[FoodTruckEvent, int]] = {}
        
        for event, score in all_parsed:
            slot_key = (event.date.date(), event.start_time)
            
            if slot_key not in best_events or score >= best_events[slot_key][1]:
                best_events[slot_key] = (event, score)
                
        # Return sorted by date
        return [e for e, s in best_events.values()]

    def _parse_vevent(self, block: str) -> List[FoodTruckEvent]:
        summary = ""
        dtstart_params = dtstart_value = ""
        recurrence_params = recurrence_value = ""
        dtend_params = dtend_value = ""
        rrule_value = ""
        last_modified_value = ""

        for line in block.strip().splitlines():
            if ":" not in line:
                continue
            params_part, _, value = line.partition(":")
            base_key = params_part.split(";")[0].upper()
            value = value.strip()

            if base_key == "SUMMARY":
                summary = value
            elif base_key == "DTSTART":
                dtstart_params, dtstart_value = params_part, value
            elif base_key == "RECURRENCE-ID":
                recurrence_params, recurrence_value = params_part, value
            elif base_key == "DTEND":
                dtend_params, dtend_value = params_part, value
            elif base_key == "RRULE":
                rrule_value = value
            elif base_key == "LAST-MODIFIED":
                last_modified_value = value

        if not summary or (not dtstart_value and not recurrence_value):
            return []

        # If RECURRENCE-ID is present, it specifies the specific occurrence date
        if recurrence_value:
            dtstart = _parse_dt(recurrence_params, recurrence_value)
            dtstart_params = recurrence_params # use recurrence params for is_date_only check
        else:
            dtstart = _parse_dt(dtstart_params, dtstart_value)
            
        dtend = _parse_dt(dtend_params, dtend_value) if dtend_value else None
        if not dtstart:
            return []

        is_date_only = "VALUE=DATE" in dtstart_params.upper()
        
        # Categorize first to see if it's a known event type (trivia, etc)
        category = _categorize(summary)
        
        # Check exclude patterns
        exclude_patterns = self.brewery.parser_config.get("exclude_patterns", [])
        for pattern in exclude_patterns:
            if re.search(pattern, summary, re.IGNORECASE):
                self.logger.debug(f"Skipping excluded event: {summary}")
                return []

        # If it's community/unknown and we have a default for this brewery, use it
        if category == "community":
            default_cat = self.brewery.parser_config.get("default_category")
            if default_cat:
                category = default_cat

        # STALE EVENT FILTER:
        # Chuck's has many old recurring events from 2013-2015.
        # We only want events that were created/updated recently OR specifically for now.
        now = datetime.now(tz=_PACIFIC).replace(tzinfo=None)
        
        # If it's an infinite recurring event, check if it's been updated in the last 2 years
        if rrule_value and "UNTIL" not in rrule_value.upper():
            if last_modified_value:
                last_mod = _parse_dt("", last_modified_value)
                if last_mod and last_mod.date() < (now - timedelta(days=365*2)).date():
                    self.logger.debug(f"Skipping ancient infinite recurring event: {summary}")
                    return []
            # Fallback if no last-modified: if started > 2 years ago, skip
            elif dtstart.date() < (now - timedelta(days=365*2)).date():
                return []

        if rrule_value:
            byday, until = _parse_rrule(rrule_value)
            if byday:
                occurrences = _expand_weekly(dtstart, dtend, byday, until)
                return [
                    self._make_event(summary, s, e, category, is_date_only=False)
                    for s, e in occurrences
                ]
            return []

        # Single event (including those with RECURRENCE-ID)
        now = datetime.now(tz=_PACIFIC).replace(tzinfo=None)
        # Only include if it's within our window (today or future)
        if dtstart.date() < now.date():
            return []

        return [self._make_event(summary, dtstart, dtend, category, is_date_only)]

    def _make_event(
        self,
        summary: str,
        start: datetime,
        end: Optional[datetime],
        category: str,
        is_date_only: bool = False,
    ) -> FoodTruckEvent:
        return FoodTruckEvent(
            brewery_key=self.brewery.key,
            brewery_name=self.brewery.name,
            food_truck_name=_clean_summary(summary),
            date=_midnight(start),
            start_time=None if is_date_only else start,
            end_time=None if is_date_only else end,
            description=None,
            category=category,
        )
