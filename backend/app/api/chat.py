import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.chatbot.service import answer
from app.core.config import settings
from app.schemas.chat import ChatReply, ChatRequest

router = APIRouter(prefix="/chat", tags=["chatbot"])

_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.CHAT_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many messages. Please wait a minute.")
    q.append(now)


@router.post("", response_model=ChatReply, dependencies=[Depends(rate_limit)])
def chat(data: ChatRequest):
    """General platform help. Not medical advice. Available without logging in."""
    return answer(data.messages)
