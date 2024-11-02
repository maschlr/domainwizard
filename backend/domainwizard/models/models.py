import datetime as dt
import enum
import hashlib
import json
import tempfile
import time

try:
    from itertools import batched  # type: ignore
except ImportError:
    from itertools import islice

    def batched(iterable, n):
        # batched('ABCDEFG', 3) → ABC DEF G
        if n < 1:
            raise ValueError("n must be at least one")
        iterator = iter(iterable)
        while batch := tuple(islice(iterator, n)):
            yield batch


from typing import Iterable, Iterator, List, Optional, Self, Sequence, Tuple

import openai
import requests
import sqlalchemy
import ulid
from loguru import logger
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ForeignKey,
    Index,
    LargeBinary,
    MetaData,
    Result,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from ulid import ULID
from urllib3.exceptions import IncompleteRead, ProtocolError
from urllib3.exceptions import TimeoutError as ConnectionTimeoutError

from ..config import config
from ..integrations.completions import get_summary
from ..integrations.embeddings import get_embeddings

client = openai.OpenAI(api_key=config["OPENAI_API_KEY"])


class Base(DeclarativeBase):
    created_at: Mapped[dt.datetime] = mapped_column(default=lambda: dt.datetime.now(dt.UTC))
    updated_at: Mapped[dt.datetime] = mapped_column(
        default=lambda: dt.datetime.now(dt.UTC),
        onupdate=lambda: dt.datetime.now(dt.UTC),
    )

    # https://alembic.sqlalchemy.org/en/latest/naming.html#integration-of-naming-conventions-into-operations-autogenerate
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Listing(Base):
    """_summary_
    A domain listing (currently only from GoDaddy listings)
    """

    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(unique=True, index=True)
    link: Mapped[str] = mapped_column()
    auction_type: Mapped[Optional[str]] = mapped_column(nullable=True)
    auction_end_time: Mapped[Optional[dt.datetime]] = mapped_column(nullable=True)
    price: Mapped[Optional[int]] = mapped_column(nullable=True)
    number_of_bids: Mapped[Optional[int]] = mapped_column(nullable=True)
    domain_age: Mapped[Optional[int]] = mapped_column(nullable=True)
    pageviews: Mapped[Optional[int]] = mapped_column(nullable=True)
    valuation: Mapped[Optional[int]] = mapped_column(nullable=True)
    monthly_parking_revenue: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_adult: Mapped[Optional[bool]] = mapped_column(nullable=True)
    # when listing is created
    embeddings: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    domain_searches: Mapped[List["DomainSearch"]] = relationship(
        "DomainSearch",
        secondary="listings_to_domain_searches_rel",
        back_populates="listings",
        overlaps="listing_domain_searches",
    )
    listing_domain_searches: Mapped[List["ListingDomainSearch"]] = relationship(
        "ListingDomainSearch", back_populates="listing", overlaps="domain_searches"
    )

    batch_request_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("openai_embedding_batch_requests.id"), nullable=True
    )
    batch_request: Mapped[Optional["OpenAIEmbeddingBatchRequest"]] = relationship(
        "OpenAIEmbeddingBatchRequest", back_populates="listings"
    )

    @classmethod
    def upsert_batch(
        cls, session: Session, listings: Iterator[Self], source: str, batch_size=100000
    ) -> Iterable[tuple[int, str]]:
        """
        Upserts a batch of listings into the database

        If the listing already exists, it will be updated with the new data
        If the listing does not exist, it will be inserted
        For all the listings that are not in the dataset anymore, remove the embeddings
        """
        tick = time.time()
        logger.info("Upserting listings from downloaded batch")
        logger.info(f"Querying database for existing listings from {source}")
        url_to_id = {
            row.url: row.id for row in session.execute(select(cls.url, cls.id).where(cls.link.like(f"%{source}%")))
        }
        urls_with_embeddings = {
            row.url
            for row in session.execute(
                select(cls.url).where(cls.embeddings.isnot(None)).where(cls.link.like(f"%{source}%"))
            )
        }
        tack = time.time()
        logger.info(f"Found {len(url_to_id)} listings in the database (took {tack - tick:.2f}s)")
        urls_to_be_deleted = set()
        logger.info(f"Processing {source} data in batches...")
        for i, url_item_batch in enumerate(batched(listings, batch_size)):
            listing_id_to_url, urls_not_in_batch = cls.process_items(
                session, url_to_id, urls_with_embeddings, url_item_batch, batch_size=batch_size // 5, n_batch=i + 1
            )
            for listing_id, url in listing_id_to_url.items():
                yield listing_id, url
            if i == 0:
                urls_to_be_deleted = urls_not_in_batch
            else:
                urls_to_be_deleted &= urls_not_in_batch

        logger.info("Deleting outdated listings...")
        for url_batch in batched(urls_to_be_deleted, batch_size // 5):
            session.execute(delete(cls).where(cls.id.in_(url_to_id[url] for url in url_batch)))
            session.flush()

    @classmethod
    def process_items(
        cls,
        session: Session,
        db_url_to_id: dict[str, int],
        urls_with_embeddings: set[str],
        url_items: Iterable[dict],
        batch_size: int,
        n_batch: int,
    ) -> tuple[dict[int, str], set[str]]:
        url_to_data = {datum["url"]: datum for datum in url_items}
        listing_urls_in_batch = url_to_data.keys()
        listing_urls_to_be_updated = listing_urls_in_batch & db_url_to_id.keys()
        new_listing_urls = listing_urls_in_batch - db_url_to_id.keys()
        urls_not_in_batch = (db_url_to_id.keys() - listing_urls_in_batch) & urls_with_embeddings

        fnames_for_update = [
            "auction_end_time",
            "price",
            "valuation",
            "number_of_bids",
        ]
        logger.info(f"Updating existing listings in batch #{n_batch}")
        for url_batch in batched(listing_urls_to_be_updated, batch_size):
            session.execute(
                update(cls),
                [
                    {
                        "id": db_url_to_id[url],
                        **{fname: url_to_data[url].get(fname) for fname in fnames_for_update},
                    }
                    for url in url_batch
                ],
            )
            session.flush()

        result_listing_id_to_url = {}
        if new_listing_urls:
            logger.info(f"Inserting new listings in batch #{n_batch}")
            for url_batch in batched(new_listing_urls, batch_size):
                new_listings = session.execute(
                    insert(cls).returning(cls.id, cls.url),
                    [url_to_data[url] for url in url_batch],
                )
                result_listing_id_to_url.update({listing.id: listing.url for listing in new_listings})
                session.flush()

        return result_listing_id_to_url, urls_not_in_batch

    @classmethod
    def get_by_embeddings(
        cls, session: Session, embeddings: List[float], limit: int = 100
    ) -> Result[Tuple[Self, float]]:
        now = dt.datetime.now(dt.UTC)
        query = (
            select(cls, cls.embeddings.cosine_distance(embeddings).label("score"))
            .where(cls.auction_end_time > now)
            .order_by(cls.embeddings.cosine_distance(embeddings))
            .limit(limit)
        )
        return session.execute(query)

    @classmethod
    def get_active_listings_count(cls, session: Session):
        now = dt.datetime.now(dt.UTC)
        # pylint: disable=not-callable
        count_query = select(func.count()).select_from(cls).where(cls.auction_end_time > now)
        row_count = session.execute(count_query).scalar()
        return row_count


ListingIndex = Index(
    "ivfflat_index",
    Listing.embeddings,
    postgresql_using="ivfflat",
    postgresql_with={"lists": 1000},
    postgresql_ops={"embeddings": "vector_cosine_ops"},
)


class DomainSearch(Base):
    """
    A request for a domain search
    """

    __tablename__ = "domain_searches"
    id: Mapped[int] = mapped_column(primary_key=True)
    ulid: Mapped[bytes] = mapped_column(LargeBinary(16), unique=True, index=True, default=lambda: bytes(ULID()))
    prompt: Mapped[str] = mapped_column()
    prompt_hash: Mapped[str] = mapped_column(unique=True)
    is_unlocked: Mapped[bool] = mapped_column(default=False)
    is_example: Mapped[bool] = mapped_column(default=False)
    summary: Mapped[Optional[str]] = mapped_column(nullable=True)
    embeddings: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    listings: Mapped[List["Listing"]] = relationship(
        "Listing",
        secondary="listings_to_domain_searches_rel",
        back_populates="domain_searches",
        overlaps="listing_domain_searches",
    )
    listing_domain_searches: Mapped[List["ListingDomainSearch"]] = relationship(
        "ListingDomainSearch", back_populates="domain_search", overlaps="listings,domain_searches"
    )
    name: Mapped[Optional[str]] = mapped_column(nullable=True)
    email: Mapped[Optional[str]] = mapped_column(nullable=True)

    @classmethod
    def get_by_uuid(cls, session: Session, uuid: str) -> Optional["DomainSearch"]:
        uuid_bytes = bytes.fromhex(uuid.replace("-", ""))
        return session.scalar(select(cls).where(cls.ulid == uuid_bytes))

    @classmethod
    def get_examples(cls, session: Session, limit=4) -> Sequence["DomainSearch"]:
        examples = session.scalars(select(cls).where(cls.is_example).limit(limit)).all()
        return examples

    @classmethod
    def create_or_get(cls, session: Session, prompt: str) -> "DomainSearch":
        prompt = prompt.strip()
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        domain_search = session.scalar(select(cls).where(cls.prompt_hash == prompt_hash))
        if domain_search is None:
            embeddings = get_embeddings(prompt)
            summary = get_summary(prompt)
            domain_search = cls(prompt=prompt, prompt_hash=prompt_hash, embeddings=embeddings, summary=summary)
            session.add(domain_search)
            domain_search.update_listings(session)
        return domain_search

    def update_listings(self, session: Session, limit=100) -> Optional[Sequence["Listing"]]:
        """Update the listings and return the ids of the listings that were updated"""
        if self.embeddings is None:
            self.embeddings = get_embeddings(self.prompt)
        existing_listings_domains_searches = self.listing_domain_searches
        existing_listing_ids = {lds.listing_id: lds for lds in existing_listings_domains_searches}
        listing_to_score = {
            listing.id: score for (listing, score) in Listing.get_by_embeddings(session, self.embeddings, limit)
        }
        updated_listing_ids = listing_to_score.keys() - existing_listing_ids.keys()
        to_remove_listing_ids = existing_listing_ids.keys() - listing_to_score.keys()

        for listing_id in updated_listing_ids:
            score = listing_to_score[listing_id]
            listing_domain_search = ListingDomainSearch(listing_id=listing_id, domain_search=self, score=score)
            session.add(listing_domain_search)

        for listing_id in to_remove_listing_ids:
            session.delete(existing_listing_ids[listing_id])

        if updated_listing_ids:
            return sorted(
                (listing for listing_id in updated_listing_ids if (listing := session.get(Listing, listing_id))),
                key=lambda listing: listing_to_score[listing.id],
                reverse=True,
            )

    @classmethod
    def create(cls, session: Session, prompt: str) -> "DomainSearch":
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        request = cls(prompt=prompt, prompt_hash=prompt_hash)
        session.add(request)
        return request

    @property
    def uuid(self) -> str:
        return str(ULID(self.ulid).to_uuid())

    def get_result(self):
        """Helper function to get the result of a domain search including the skeletons if the request is not unlocked"""
        offset = 0 if self.is_unlocked else 5
        listing_id_to_score = {
            listing_domain_search.listing.id: listing_domain_search.score
            for listing_domain_search in self.listing_domain_searches
        }
        sorted_domain_listings = sorted(
            self.listings, key=lambda listing: listing_id_to_score[listing.id], reverse=True
        )
        result = {
            "domains": [
                {
                    "rank": i,
                    "url": listing.url,
                    "pageviews": listing.pageviews,
                    "valuation": listing.valuation,
                    "monthlyParkingRevenue": listing.monthly_parking_revenue,
                    "isAdult": listing.is_adult,
                    "link": listing.link,
                    "auctionType": listing.auction_type,
                    "auctionEndTime": (
                        listing.auction_end_time.replace(tzinfo=dt.UTC).isoformat()
                        if listing.auction_end_time
                        else None
                    ),
                    "auctionEndTimeEpoch": (
                        int(listing.auction_end_time.timestamp()) if listing.auction_end_time else None
                    ),
                    "price": listing.price,
                    "numberOfBids": listing.number_of_bids,
                    "domainAge": listing.domain_age,
                    "score": listing_id_to_score[listing.id],
                }
                for i, listing in enumerate(sorted_domain_listings[offset:], start=offset + 1)
            ],
            "uuid": self.uuid,
            "totalDomains": len(self.listings),
            "isUnlocked": self.is_unlocked,
            "prompt": self.prompt,
            "summary": self.summary,
        }
        if not self.is_unlocked:
            result["skeletons"] = [
                {
                    "rank": i,
                    "price": listing.price,
                    "pageviews": listing.pageviews,
                    "valuation": listing.valuation,
                    "score": listing_id_to_score[listing.id],
                }
                for i, listing in enumerate(sorted_domain_listings[:offset], start=1)
            ]
        else:
            result["skeletons"] = []

        return result

    @classmethod
    def get_all(cls, session: Session) -> Sequence["DomainSearch"]:
        return session.scalars(select(cls)).all()

    @classmethod
    def get_count(cls, session: Session) -> int:
        count = session.scalar(select(func.count()).select_from(cls))
        if count is None:
            return 0
        else:
            return count


class ListingDomainSearch(Base):
    __tablename__ = "listings_to_domain_searches_rel"

    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True)
    domain_search_id: Mapped[int] = mapped_column(ForeignKey("domain_searches.id"), primary_key=True)
    listing: Mapped["Listing"] = relationship(
        Listing, back_populates="listing_domain_searches", overlaps="domain_searches,listings"
    )
    domain_search: Mapped["DomainSearch"] = relationship(
        DomainSearch, back_populates="listing_domain_searches", overlaps="listings,domain_searches"
    )

    score: Mapped[float] = mapped_column()


class BatchRequestStatus(enum.Enum):
    PENDING = 0  # created but not submitted
    PROCESSING = 1  # submitted to openai
    COMPLETED = 2  # completed but not downloaded
    FAILED = 3  # failed
    FINALIZED = 4  # inserted into database


class OpenAIEmbeddingBatchRequest(Base):
    __tablename__ = "openai_embedding_batch_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[str] = mapped_column(unique=True)
    listings: Mapped[List[Listing]] = relationship("Listing", back_populates="batch_request")
    status: Mapped[BatchRequestStatus] = mapped_column(default=BatchRequestStatus.PENDING)
    output_file_id: Mapped[Optional[str]] = mapped_column(nullable=True)

    @property
    def output_file_id_download_url(self) -> str:
        if self.output_file_id is None:
            raise ValueError("No output file id on {self.batch_id}")
        url = f"https://api.openai.com/v1/internal/files/{self.output_file_id}/download_link"
        headers = {"Authorization": f"Bearer {config['OPENAI_API_KEY']}"}
        download_link_response = requests.get(url, headers=headers, timeout=5)
        return download_link_response.json()["url"]

    @classmethod
    def create_batch_requests(
        cls,
        session: Session,
        listing_id_to_url: Iterable[tuple[int, str]],
        batch_size: int = 50000,
    ):
        """
        Create a batch request for the given listings
        """
        for i, listing_batch in enumerate(batched(listing_id_to_url, batch_size)):
            logger.info(f"Creating OpenAI text embedding batch request #{i+1}")
            with tempfile.TemporaryFile() as buffer:
                for listing_id, url in listing_batch:
                    parts = url.split(".")
                    request_data = {
                        "custom_id": f"{str(ulid.ULID())}:{listing_id}:{url}",
                        "method": "POST",
                        "url": "/v1/embeddings",
                        "body": {
                            "model": "text-embedding-3-small",
                            "input": [" ".join(parts)],
                            "encoding_format": "float",
                        },
                    }
                    buffer.write((json.dumps(request_data) + "\n").encode("utf-8"))
                buffer.seek(0)

                batch_input_file = client.files.create(file=buffer, purpose="batch")
                request_response = client.batches.create(
                    input_file_id=batch_input_file.id,
                    endpoint="/v1/embeddings",
                    completion_window="24h",
                )
                batch_request = cls(
                    batch_id=request_response.id,
                    status=BatchRequestStatus.PROCESSING,
                )
                session.add(batch_request)
                session.flush()
                session.execute(
                    update(Listing),
                    [{"id": listing_id, "batch_request_id": batch_request.id} for listing_id, _ in listing_batch],
                )

    @classmethod
    def update_processing(cls, session: Session) -> list["OpenAIEmbeddingBatchRequest"]:
        """
        Process all the open batch requests
        """
        result = []
        open_batch_requests = session.scalars(
            select(cls).where(cls.status.in_([BatchRequestStatus.PENDING, BatchRequestStatus.PROCESSING]))
        )
        now = dt.datetime.now(dt.UTC)
        for batch_request in open_batch_requests:
            batch_response = client.batches.retrieve(batch_request.batch_id)
            if batch_response.status == "completed":
                logger.info(f"Batch {batch_request.batch_id} completed!")
                batch_request.output_file_id = batch_response.output_file_id
                batch_request.status = BatchRequestStatus.COMPLETED
                result.append(batch_request)
            elif batch_response.status == "failed":
                created_at = dt.datetime.fromtimestamp(batch_response.created_at, tz=dt.UTC)
                logger.error(f"Batch {batch_request.batch_id} failed!")
                if now - created_at < dt.timedelta(days=2):
                    logger.warning(f"Batch {batch_request.batch_id} failed within last 48 hours, retrying")
                    listing_id_to_url = (
                        (listing_id, listing_url)
                        for listing_id, listing_url in session.execute(
                            select(Listing.id, Listing.url).where(Listing.batch_request_id == batch_request.id)
                        )
                    )
                    cls.create_batch_requests(session, listing_id_to_url)
                batch_request.status = BatchRequestStatus.FAILED
        return result

    def download(self, session_factory: sessionmaker, retry=1, max_retries=3, batch_size=10000):
        with session_factory.begin() as session:
            session.add(self)
            download_url = self.output_file_id_download_url
            embedding_file_response = requests.get(download_url, stream=True, timeout=5)
            session.add(self)
            # pylint: disable=not-callable
            count_query = select(func.count()).select_from(Listing).where(Listing.batch_request_id == self.id)
            n_listings = session.execute(count_query).scalar()
            batch_id = self.batch_id
        try:
            for data_batch in batched(self._yield_embedding_data(embedding_file_response, batch_id), batch_size):
                with session_factory.begin() as session:
                    try:
                        session.execute(
                            update(Listing),
                            [{"id": listing_id, "embeddings": embeddings} for listing_id, embeddings in data_batch],
                        )
                    except sqlalchemy.orm.exc.StaleDataError as e:
                        logger.warning(f"Skipping batch with {len(data_batch)} entries ({e})")
                        continue

        except (
            TimeoutError,
            IncompleteRead,
            ConnectionTimeoutError,
            requests.exceptions.ConnectionError,
            ProtocolError,
        ):
            if retry < max_retries:
                logger.warning(f"Download failed for {batch_id}. Retrying {retry}/{max_retries}")
                return self.download(session_factory, retry=retry + 1, max_retries=max_retries, batch_size=batch_size)
            else:
                raise

        with session_factory.begin() as session:
            session.add(self)
            self.status = BatchRequestStatus.FINALIZED
            if self.output_file_id:
                logger.info(
                    f"Downloaded embeddings for {n_listings} listings in {self.batch_id}. Deleting file {self.output_file_id}"
                )
                client.files.delete(self.output_file_id)

    @staticmethod
    def _yield_embedding_data(response: requests.Response, batch_id: str) -> Iterable[tuple[int, list[float]]]:
        logger.info(f"Downloading & processing lines in {batch_id}")
        for line in response.iter_lines(decode_unicode=True):
            data = json.loads(line)
            custom_id = data["custom_id"]
            _ulid, listing_id, _url = custom_id.split(":")
            embeddings = data["response"]["body"]["data"][0]["embedding"]
            yield listing_id, embeddings


class DataUpdate(Base):
    __tablename__ = "data_updates"
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_count: Mapped[int] = mapped_column()
    domain_search_count: Mapped[int] = mapped_column()

    @classmethod
    def get_listing_count(cls, session: Session):
        latest_update = session.scalar(select(cls).order_by(cls.created_at.desc()).limit(1))
        return latest_update.listing_count
