import datetime as dt
import re
import tempfile
import zipfile
from typing import Any, Iterator

import ijson
import requests
from loguru import logger

from .domains import DomainAdapter

DOLLAR_PATTERN = re.compile(r"\$(\d+)")


class GodaddyAdapter(DomainAdapter):
    url = "https://inventory.auctions.godaddy.com/all_listings.json.zip"
    name = "godaddy"

    def yield_listings_data(self) -> Iterator[dict[str, Any]]:
        response = requests.get(self.url, stream=True, timeout=10)
        # Sizes in bytes.
        block_size = 1024
        with tempfile.TemporaryFile() as buffer:
            logger.info("Downloading Godaddy domain auctions")
            for chunk in response.iter_content(block_size):
                buffer.write(chunk)

            logger.info("Downloaded dataset from Godaddy. Extracting...")
            buffer.seek(0)
            with zipfile.ZipFile(buffer, "r") as myzip:
                [json_file] = myzip.namelist()
                with myzip.open(json_file) as myfile:
                    for item in ijson.items(myfile, "data.item"):
                        listing_data = self.transform_item(item)
                        if self.item_filter(listing_data["url"]):
                            yield listing_data

    @staticmethod
    def transform_item(domaindatum: dict[str, Any]) -> dict[str, Any]:
        keys_to_transform = {
            "domainName": ("url", lambda x: x.lower()),
            "auctionEndTime": (
                "auction_end_time",
                lambda dt_str: dt.datetime.fromisoformat(dt_str).replace(tzinfo=dt.UTC),
            ),
            "price": ("price", lambda x: match.group(1) if (match := DOLLAR_PATTERN.match(x)) else None),
            "valuation": ("valuation", lambda x: match.group(1) if (match := DOLLAR_PATTERN.match(x)) else None),
            "monthlyParkingRevenue": (
                "monthly_parking_revenue",
                lambda x: match.group(1) if (match := DOLLAR_PATTERN.match(x)) else None,
            ),
        }
        keys_to_fname = {
            "link": "link",
            "auctionType": "auction_type",
            "numberOfBids": "number_of_bids",
            "domainAge": "domain_age",
            "pageviews": "pageviews",
            "isAdult": "is_adult",
        }
        fields_to_data = {}
        for key, value in domaindatum.items():
            if key in keys_to_transform:
                model_fname, fnc = keys_to_transform[key]
                fields_to_data[model_fname] = fnc(value)
            else:
                fname = keys_to_fname[key]
                fields_to_data[fname] = value
        return fields_to_data
