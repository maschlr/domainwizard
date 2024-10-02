from domainwizard.integrations.godaddy import yield_listing_items
from domainwizard.models import Listing, OpenAIEmbeddingBatchRequest, Session
from loguru import logger

if __name__ == "__main__":
    dataset = yield_listing_items()
    logger.info(
        "Downloaded dataset from Godaddy. Starting database upsert...",
    )
    with Session.begin() as session:
        listing_id_to_url = Listing.upsert_batch(session, dataset)
        if listing_id_to_url:
            OpenAIEmbeddingBatchRequest.create_batch_requests(session, listing_id_to_url)
