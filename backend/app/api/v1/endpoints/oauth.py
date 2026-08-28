"""SMART on FHIR OAuth 2.0 endpoints with PKCE."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.config import settings
from app.core.deps import DbSession
from app.core.jwks import get_jwks_manager
from app.services.oauth_service import OAuthService

router = APIRouter()
client_auth = HTTPBasic(auto_error=False)


def _verify_client(credentials: HTTPBasicCredentials | None, client_id: str | None) -> str:
    if credentials:
        cid, secret = credentials.username, credentials.password
    elif client_id:
        cid = client_id
        secret = settings.OAUTH_CLIENTS.get(client_id, "")
    else:
        raise HTTPException(status_code=401, detail="Client authentication required")
    expected = settings.OAUTH_CLIENTS.get(cid)
    if not expected or not secrets.compare_digest(expected, secret or ""):
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    return cid


@router.get("/.well-known/smart-configuration")
async def smart_configuration():
    base = settings.OAUTH_ISSUER.rstrip("/")
    return {
        "issuer": base,
        "jwks_uri": f"{base}/.well-known/jwks.json",
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "introspection_endpoint": f"{base}/oauth/introspect",
        "revocation_endpoint": f"{base}/oauth/revoke",
        "capabilities": [
            "launch-ehr",
            "launch-standalone",
            "client-public",
            "client-confidential-symmetric",
            "context-ehr-patient",
            "permission-v2",
        ],
        "scopes_supported": [
            "launch",
            "launch/patient",
            "patient/Patient.read",
            "patient/Coverage.read",
            "user/CoverageEligibilityRequest.write",
            "user/Claim.write",
            "system/Claim.write",
        ],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
    }


@router.get("/.well-known/jwks.json")
async def jwks():
    return get_jwks_manager().jwks_document()


@router.get("/oauth/authorize")
async def oauth_authorize(
    db: DbSession,
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(...),
    state: str = Query(...),
    code_challenge: str = Query(...),
    code_challenge_method: str = Query(default="S256"),
    aud: str | None = Query(default=None),
    launch: str | None = Query(default=None),
    patient: str | None = Query(default=None),
):
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")
    if code_challenge_method != "S256":
        raise HTTPException(status_code=400, detail="Only S256 PKCE supported")
    if client_id not in settings.OAUTH_CLIENTS:
        raise HTTPException(status_code=400, detail="Unknown client_id")

    # Dev scaffold: auto-approve consent; production renders consent UI
    subject_id = "practitioner-001"
    patient_id = patient or (f"Patient/{launch}" if launch else None)

    service = OAuthService(db)
    code = await service.create_authorization_code(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
        subject_id=subject_id,
        patient_id=patient_id,
        launch=launch,
    )
    location = service.build_redirect_uri(redirect_uri, code, state)
    return RedirectResponse(url=location, status_code=status.HTTP_302_FOUND)


@router.post("/oauth/token")
async def oauth_token(
    db: DbSession,
    grant_type: Annotated[str, Form()],
    code: Annotated[str | None, Form()] = None,
    redirect_uri: Annotated[str | None, Form()] = None,
    client_id: Annotated[str | None, Form()] = None,
    code_verifier: Annotated[str | None, Form()] = None,
):
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")
    if not all([code, redirect_uri, client_id, code_verifier]):
        raise HTTPException(status_code=400, detail="Missing required parameters")

    service = OAuthService(db)
    return await service.exchange_authorization_code(
        code=code,
        redirect_uri=redirect_uri,
        client_id=client_id,
        code_verifier=code_verifier,
    )


@router.post("/oauth/introspect")
async def oauth_introspect(
    db: DbSession,
    token: Annotated[str, Form()],
    credentials: Annotated[HTTPBasicCredentials | None, Depends(client_auth)] = None,
    client_id: Annotated[str | None, Form()] = None,
    client_secret: Annotated[str | None, Form()] = None,
):
    cid = _verify_client(credentials, client_id)
    if client_secret and not secrets.compare_digest(settings.OAUTH_CLIENTS.get(cid, ""), client_secret):
        raise HTTPException(status_code=401, detail="Invalid client credentials")
    service = OAuthService(db)
    return await service.introspect_token(token)


@router.post("/oauth/revoke")
async def oauth_revoke(
    db: DbSession,
    token: Annotated[str, Form()],
    credentials: Annotated[HTTPBasicCredentials | None, Depends(client_auth)] = None,
    client_id: Annotated[str | None, Form()] = None,
):
    _verify_client(credentials, client_id)
    service = OAuthService(db)
    await service.revoke_token(token)
    return {"status": "revoked"}
