import csv
import datetime as dt
import io
import re
import tempfile
from typing import Any, Iterator

import requests
from loguru import logger

from .domains import DomainAdapter

DOLLAR_PATTERN = re.compile(r"\$(\d+)")
CONTAINS_MORE_THAN_TWO_NUMBERS_PATTERN = re.compile(r".*?\d{3,}.*?$")


class NamecheapAdapter(DomainAdapter):
    # only auctions
    # TODO: get direct sale listings
    url = "https://nc-aftermarket-www-production.s3.amazonaws.com/reports/Namecheap_Market_Sales.csv"
    name = "namecheap"

    def yield_listings_data(self) -> Iterator[dict[str, Any]]:
        response = requests.get(self.url, stream=True, timeout=10)
        # Sizes in bytes.
        block_size = 1024
        with tempfile.TemporaryFile() as buffer:
            logger.info("Downloading Namecheap domain auctions")
            for chunk in response.iter_content(block_size):
                buffer.write(chunk)

            logger.info("Downloaded dataset from Namecheap. Processing listings..")
            buffer.seek(0)

            string_buffer = io.TextIOWrapper(buffer, encoding="utf-8")
            reader = csv.DictReader(string_buffer)
            for row in reader:
                listing_data = self.transform_item(row)
                if self.item_filter(listing_data["url"]):
                    yield listing_data

    @staticmethod
    def transform_item(domaindatum: dict[str, Any]) -> dict[str, Any]:
        return {
            "url": domaindatum["name"],
            "link": domaindatum["url"],
            "auction_type": "Bid",
            "auction_end_time": dt.datetime.fromisoformat(domaindatum["endDate"]).replace(tzinfo=dt.UTC),
            "price": int(float(domaindatum["price"])),
            "number_of_bids": int(domaindatum["bidCount"]),
            "domain_age": (
                dt.datetime.fromisoformat(domaindatum["registeredDate"]).replace(tzinfo=dt.UTC)
                - dt.datetime.now(dt.UTC)
            ).days
            // 365,
            "valuation": int(float(domaindatum.get("lastSoldPrice") or domaindatum.get("estibotValue") or 0)),
        }
