from domainwizard.integrations.email import send_update_email
from domainwizard.models import (
    BatchRequestStatus,
    DomainSearch,
    OpenAIEmbeddingBatchRequest,
    Session,
)
from sqlalchemy import select
from tqdm import tqdm

if __name__ == "__main__":
    with Session.begin() as session:
        completed_batch_requests = OpenAIEmbeddingBatchRequest.update_processing(session)
        if not completed_batch_requests:
            completed_batch_requests = session.scalars(
                select(OpenAIEmbeddingBatchRequest).where(
                    OpenAIEmbeddingBatchRequest.status == BatchRequestStatus.COMPLETED
                )
            ).all()

    for batch_request in tqdm(completed_batch_requests, desc="Downloading completed batch requests"):
        with Session.begin() as session:
            session.add(batch_request)
            batch_request.download(session, batch_size=500)
            session.flush()
            unlocked_domain_searches = DomainSearch.get_unlocked(session)
            for domain_search in unlocked_domain_searches:
                updated_listings = domain_search.update_listings(session)
                if updated_listings and domain_search.email and domain_search.name:
                    send_update_email(domain_search, updated_listings)
