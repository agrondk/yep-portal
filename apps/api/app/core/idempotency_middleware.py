import json
from collections.abc import Awaitable, Callable
from typing import cast

from fastapi import Request, Response
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.core.database import SessionLocal
from app.core.idempotency import replay_or_none, save_response
from app.core.security import hash_token
from app.modules.core.models import UserSession


class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        key = request.headers.get("Idempotency-Key")
        token = request.cookies.get("yep_session")
        if request.method != "POST" or not key or not token:
            return await call_next(request)
        route = request.url.path
        with SessionLocal() as db:
            session = db.scalar(
                select(UserSession).where(UserSession.token_hash == hash_token(token))
            )
            if session is None:
                return await call_next(request)
            replay = replay_or_none(db, key=key, user_id=session.user_id, route=route)
            if replay is not None:
                return Response(
                    content=json.dumps(replay.response_body),
                    status_code=replay.status_code,
                    media_type="application/json",
                    headers={"Idempotency-Replayed": "true"},
                )
            response = await call_next(request)
            streaming_response = cast(StreamingResponse, response)
            body_buffer = bytearray()
            async for chunk in streaming_response.body_iterator:
                body_buffer.extend(chunk.encode() if isinstance(chunk, str) else bytes(chunk))
            body = bytes(body_buffer)
            if response.status_code < 500:
                try:
                    parsed = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    parsed = {"raw": body.decode("utf-8", errors="replace")}
                save_response(
                    db,
                    key=key,
                    user_id=session.user_id,
                    route=route,
                    body=parsed,
                    status_code=response.status_code,
                )
                db.commit()
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
