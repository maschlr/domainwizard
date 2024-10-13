from domainwizard.integrations.email import send_update_email
from domainwizard.models import (
    BatchRequestStatus,
    DomainSearch,
    OpenAIEmbeddingBatchRequest,
    Session,
)
from loguru import logger
from sqlalchemy import select

if __name__ == "__main__":
    with Session.begin() as session:
        completed_batch_requests = OpenAIEmbeddingBatchRequest.update_processing(session)
        if not completed_batch_requests:
            completed_batch_requests = session.scalars(
                select(OpenAIEmbeddingBatchRequest).where(
                    OpenAIEmbeddingBatchRequest.status == BatchRequestStatus.COMPLETED
                )
            ).all()

    updated = False
    logger.info("Downloading completed batch requests")
    for batch_request in completed_batch_requests:
        batch_request.download(Session, batch_size=5000)
        updated = True

    if updated:
        with Session.begin() as session:
            domain_searches = DomainSearch.get_all(session)
            for domain_search in domain_searches:
                updated_listings = domain_search.update_listings(session)
                if (
                    updated_listings is not None
                    and domain_search.is_unlocked
                    and domain_search.email
                    and domain_search.name
                ):
                    send_update_email(domain_search, updated_listings)
