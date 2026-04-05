import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

_bearer = HTTPBearer(auto_error=False)

_LOCAL_IPS = {"127.0.0.1", "::1", "localhost"}


async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str | None:
    # Skip auth for local requests when configured
    if settings.LOCAL_NO_AUTH:
        client_ip = request.client.host if request.client else None
        if client_ip in _LOCAL_IPS:
            return None

    if credentials is None or not secrets.compare_digest(
        credentials.credentials, settings.API_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials
