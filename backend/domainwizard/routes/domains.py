from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from ..models import DataUpdate, DomainSearch, Session

router = APIRouter()


@router.get("/api/requests")
async def list_requests():
    with Session.begin() as session:
        requests = session.scalars(select(DomainSearch))
        return sorted(
            (
                {"uuid": request.uuid, "summary": request.summary, "isExample": request.is_example}
                for request in requests
            ),
            key=lambda x: (1 if x["isExample"] else 0, x["uuid"]),
            reverse=True,
        )


@router.put("/api/requests/{uuid}")
async def update_request(uuid: str, data: dict):
    with Session.begin() as session:
        request = DomainSearch.get_by_uuid(session, uuid)
        if request is None:
            raise HTTPException(status_code=404, detail="Request not found")
        request.is_example = data["isExample"]
        return request.get_result()


@router.get("/api/requests/{uuid}")
async def get_request(uuid: str):
    with Session.begin() as session:
        request = DomainSearch.get_by_uuid(session, uuid)
        if request is None:
            raise HTTPException(status_code=404, detail="Request not found")
        return request.get_result()


@router.get("/api/count")
async def get_active_listings_count():
    with Session.begin() as session:
        return DataUpdate.get_listing_count(session)


class DomainSearchRequestBody(BaseModel):
    prompt: str


@router.post("/api/requests")
async def create_or_get_request(data: DomainSearchRequestBody):
    """Create a new request or get an existing one"""
    with Session.begin() as session:
        request = DomainSearch.create_or_get(session, data.prompt)
        return request.get_result()


@router.get("/api/examples")
async def list_examples():
    with Session.begin() as session:
        examples = DomainSearch.get_examples(session)
        return [{"uuid": example.uuid, "prompt": example.prompt, "summary": example.summary} for example in examples]
