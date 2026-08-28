"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import eligibility, nlp, prior_authorization

api_router = APIRouter()

api_router.include_router(
    prior_authorization.router,
    prefix="/prior-authorization",
    tags=["Prior Authorization"],
)
api_router.include_router(
    eligibility.router,
    prefix="/patient",
    tags=["Patient Eligibility"],
)
api_router.include_router(
    nlp.router,
    prefix="/nlp",
    tags=["Clinical NLP"],
)

api_v1_router = api_router
