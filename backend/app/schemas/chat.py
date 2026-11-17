from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)

    @field_validator("messages")
    @classmethod
    def last_is_user(cls, v: list[ChatMessage]) -> list[ChatMessage]:
        if v[-1].role != "user":
            raise ValueError("The last message must be from the user")
        return v


class ChatAction(BaseModel):
    label: str
    to: str


class ChatReply(BaseModel):
    reply: str
    refused: bool = False
    source: Literal["guardrail", "llm", "faq"]
    actions: list[ChatAction] = []
