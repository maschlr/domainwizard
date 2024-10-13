from domainwizard.integrations.data import Adapters
from domainwizard.models import Listing, OpenAIEmbeddingBatchRequest, Session
from loguru import logger

if __name__ == "__main__":
    for Adapter in Adapters:
        adapter = Adapter()
        dataset = adapter.yield_listings_data()
        logger.info(
            f"Downloaded dataset from {adapter.name}. Starting database upsert...",
        )
        with Session.begin() as session:
            new_listing_id_to_url = Listing.upsert_batch(session, dataset)
            if new_listing_id_to_url:
                OpenAIEmbeddingBatchRequest.create_batch_requests(session, new_listing_id_to_url)
