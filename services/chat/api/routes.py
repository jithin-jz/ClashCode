import logging

from core.auth import get_token, verify_jwt
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat")


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    return JSONResponse(content={"status": "ok", "service": "chat"}, status_code=status.HTTP_200_OK)


@router.get("/history/{room}")
async def get_message_history(
    request: Request,
    room: str,
    limit: int = 50,
    last_timestamp: str | None = None,
):
    """Get paginated message history for a room."""
    token = get_token(request)
    payload = verify_jwt(token or "")
    if not payload:
        return JSONResponse(content={"error": "Invalid token"}, status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        data = await ChatService.get_history(room, limit, last_timestamp)
        return JSONResponse(content=data, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error fetching message history: {e}", exc_info=True)
        return JSONResponse(
            content={"error": "Failed to fetch message history"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/search/{room}")
async def search_room_messages(
    request: Request,
    room: str,
    q: str,
    limit: int = 20,
):
    """Search messages in a room."""
    token = get_token(request)
    payload = verify_jwt(token or "")
    if not payload:
        return JSONResponse(content={"error": "Invalid token"}, status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        from core.serializers import serialize_dynamo_message
        from dynamo import dynamo_client

        result = await dynamo_client.search_messages(room, q, limit)
        if not result.get("ok"):
            return JSONResponse(
                content={"error": "Search failed"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        messages = [serialize_dynamo_message(room, m) for m in result["items"]]
        return JSONResponse(content={"messages": messages}, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error searching messages: {e}", exc_info=True)
        return JSONResponse(
            content={"error": "Search failed"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
