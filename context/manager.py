from typing import Any

from prompts.system_prompt import get_system_prompt
from dataclasses import dataclass, field

from utils.text import count_tokens


@dataclass
class MessageItem:
    role: str
    content: str
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    token_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"role": self.role}
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id

        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        if self.content:
            result["content"] = self.content
        return result


class ContextManager:
    def __init__(self) -> None:
        self._system_prompt = get_system_prompt()
        self._messages: list[MessageItem] = []
        self._model_name = "mistralai/mistral-small-3.1-24b-instruct:free"

    def add_user_message(self, content: str) -> None:
        item = MessageItem(
            role="user",
            content=content,
            token_count=count_tokens(content, self._model_name),
        )
        self._messages.append(item)

    def add_assistant_message(self, content: str | None) -> None:
        item = MessageItem(
            role="assistant",
            content=content or "",
            token_count=count_tokens(content or "", self._model_name) if content else 0,
        )
        self._messages.append(item)

    def get_messages(self) -> list[dict[str, Any]]:
        message = []
        if self._system_prompt:
            message.append({"role": "system", "content": self._system_prompt})

        for item in self._messages:
            message.append(item.to_dict())

        return message

    def add_tool_results(self, tool_call_id: str, content: str) -> None:
        item = MessageItem(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            token_count=count_tokens(content, self._model_name),
        )
        self._messages.append(item)
