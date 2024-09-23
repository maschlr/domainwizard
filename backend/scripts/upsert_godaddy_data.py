from domainwizard.integrations.godaddy import download_dataset
from domainwizard.models import Listing, OpenAIEmbeddingBatchRequest, Session

if __name__ == "__main__":
    dataset = download_dataset()
    with Session.begin() as session:
        listing_id_to_url = Listing.upsert_batch(session, dataset)
        if listing_id_to_url:
            OpenAIEmbeddingBatchRequest.create_batch_requests(session, listing_id_to_url)
