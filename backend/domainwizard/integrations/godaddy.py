import tempfile
import zipfile
from typing import Any, Iterator

import ijson
import requests
from loguru import logger
from tqdm import tqdm

URL = "https://inventory.auctions.godaddy.com/all_listings.json.zip"


def yield_listing_items() -> Iterator[dict[str, Any]]:
    response = requests.get(URL, stream=True, timeout=10)
    # Sizes in bytes.
    total_size = int(response.headers.get("content-length", 0))
    block_size = 1024
    with tempfile.TemporaryFile() as buffer:
        with tqdm(
            total=total_size, unit="B", unit_scale=True, desc="Downloading Godaddy domain auctions"
        ) as progress_bar:
            for chunk in response.iter_content(block_size):
                progress_bar.update(len(chunk))
                buffer.write(chunk)

        logger.info("Downloaded dataset from Godaddy. Extracting...")
        buffer.seek(0)
        with zipfile.ZipFile(buffer, "r") as myzip:
            [json_file] = myzip.namelist()
            with myzip.open(json_file) as myfile:
                listings = ijson.items(myfile, "data.item")
                yield from listings
