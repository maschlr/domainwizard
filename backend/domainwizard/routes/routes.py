from fastapi import FastAPI

from . import domains, payment

app = FastAPI()


app.include_router(domains.router)
app.include_router(payment.router)
