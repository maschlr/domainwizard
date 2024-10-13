import re
from abc import ABC, abstractmethod
from typing import Any, Iterator

CONTAINS_MORE_THAN_TWO_NUMBERS_PATTERN = re.compile(r".*?\d{3,}.*?$")


class DomainAdapter(ABC):
    url: str
    name: str

    @abstractmethod
    def yield_listings_data(self) -> Iterator[dict[str, Any]]:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def transform_item(item: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def item_filter(url: str):
        """
        Returns True when the url should be upserted, False otherwise
        """
        return not bool(CONTAINS_MORE_THAN_TWO_NUMBERS_PATTERN.match(url))
