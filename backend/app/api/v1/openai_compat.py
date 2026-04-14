import time
import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_rag_service

router = APIRouter(tags=["openai-compat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "canon-builder"
    messages: list[ChatMessage]
    temperature: float = 0.3
    max_tokens: int = 2048
    stream: bool = False
    project_id: str | None = None


@router.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    rag_service=Depends(get_rag_service),
):
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        question = ""
    else:
        question = user_messages[-1].content

    result = await rag_service.query(question=question, project_id=request.project_id)

    answer = result["answer"]
    if result["citations"]:
        answer += "\n\n---\n**Sources:**\n"
        for i, cite in enumerate(result["citations"], 1):
            answer += f"{i}. {cite['title']} (relevance: {cite['relevance_score']:.2f})\n"

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "canon-builder",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": answer},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


@router.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "canon-builder",
                "object": "model",
                "created": 0,
                "owned_by": "canon-builder",
            }
        ],
    }
