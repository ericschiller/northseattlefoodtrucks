from typing import Dict, Type

from .bale_breaker import BaleBreakerParser
from .base import BaseParser
from .chucks_greenwood import ChucksGreenwoodParser
from .google_calendar import GoogleCalendarParser
from .hellbent import HellbentParser
from .lucky_envelope import LuckyEnvelopeParser
from .obec_brewing import ObecBrewingParser
from .seattle_food_truck import SeattleFoodTruckParser
from .squarespace_events import SquarespaceEventsParser
from .stoup_ballard import StoupBallardParser
from .urban_family import UrbanFamilyParser
from .wa_food_trucks import WaFoodTrucksParser
from .wheelie_pop import WheeliePopParser


class ParserRegistry:
    _parsers: Dict[str, Type[BaseParser]] = {
        "stoup-ballard": StoupBallardParser,
        "yonder-balebreaker": SquarespaceEventsParser,
        "obec-brewing": ObecBrewingParser,
        "urban-family": UrbanFamilyParser,
        "wheelie-pop": WheeliePopParser,
        "chucks-greenwood": ChucksGreenwoodParser,
        "salehs-corner": SeattleFoodTruckParser,
        "broadview-taphouse": SeattleFoodTruckParser,
        "broadview-taphouse-events": GoogleCalendarParser,
        "ridgecrest-pub": SquarespaceEventsParser,
        "ravenna-brewing": SquarespaceEventsParser,
        "halcyon-brewing": SquarespaceEventsParser,
        "lucky-envelope": LuckyEnvelopeParser,
        "shoreline-cc": WaFoodTrucksParser,
        "hellbent": GoogleCalendarParser,
    }

    @classmethod
    def get_parser(cls, key: str) -> Type[BaseParser]:
        if key not in cls._parsers:
            raise ValueError(f"No parser found for key: {key}")
        return cls._parsers[key]

    @classmethod
    def register_parser(cls, key: str, parser_class: Type[BaseParser]) -> None:
        cls._parsers[key] = parser_class

    @classmethod
    def get_supported_keys(cls) -> list:
        return list(cls._parsers.keys())
