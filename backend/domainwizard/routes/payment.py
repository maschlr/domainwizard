import asyncio

import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from loguru import logger
from pydantic import BaseModel

from ..config import config
from ..models import DomainSearch, Session

stripe.api_key = config["STRIPE_API_KEY"]

router = APIRouter()


class UnlockRequestBody(BaseModel):
    email: str
    name: str


@router.post("/api/requests/{uuid}/unlock")
async def create_checkout(uuid: str, data: UnlockRequestBody):
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": config["STRIPE_PRICE_ID"],
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=config["DOMAIN"] + f"/api/payment/{uuid}/success/",
            cancel_url=config["DOMAIN"] + f"/api/payment/{uuid}/cancel/",
            automatic_tax={"enabled": True},
            client_reference_id=uuid,
        )
        with Session.begin() as session:
            domain_search = DomainSearch.get_by_uuid(session, uuid)
            if domain_search is None:
                raise HTTPException(status_code=404, detail="Request not found")
            elif domain_search.is_unlocked:
                raise HTTPException(status_code=409, detail="Request already unlocked")
            domain_search.email = data.email
            domain_search.name = data.name
        return {"url": checkout_session.url}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session") from e


@router.post("/api/payment/webhook")
async def webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, config["STRIPE_WEBHOOK_SECRET"])
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.SignatureVerificationError as e:
        logger.error("Invalid signature")
        raise e

    # Handle the event
    if event["type"] == "checkout.session.completed":
        with Session.begin() as session:
            domain_search = DomainSearch.get_by_uuid(session, event["data"]["object"]["client_reference_id"])
            if domain_search is None:
                logger.error("Request not found")
                raise HTTPException(status_code=500, detail="Failed to create checkout session")
            domain_search.is_unlocked = True
    else:
        print("Unhandled event type {}".format(event["type"]))


@router.get("/api/payment/{uuid}/success/", response_class=RedirectResponse, status_code=303)
async def success(uuid: str):
    # check if invoice is paid
    # create async wait until invoice is paid
    with Session.begin() as session:
        domain_search = DomainSearch.get_by_uuid(session, uuid)
        if domain_search is None:
            logger.error("Request not found")
            raise HTTPException(status_code=500, detail="Failed to create checkout session")
        if not domain_search.is_unlocked:
            await asyncio.sleep(1)
            return await success(uuid)
    return config["DOMAIN"] + "/" + uuid


@router.get("/api/payment/{uuid}/cancel/", response_class=RedirectResponse, status_code=303)
async def cancel(uuid: str):
    return config["DOMAIN"] + "/" + uuid
