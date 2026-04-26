import logging
import traceback

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .exceptions import AdminBaseException

logger = logging.getLogger("clashcode.admin")


def admin_exception_handler(exc, context):
    """
    Custom exception handler for the administration module.
    Captures custom AdminBaseException and standard DRF exceptions.
    """
    # Call DRF's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)

    # If it's one of our custom administrative exceptions, DRF handler won't know it
    # unless it inherits from APIException (which ours do), but we want to add extra logging.
    if isinstance(exc, AdminBaseException):
        logger.warning(f"Admin Action Warning: {exc.detail} | User: {context['request'].user} | Path: {context['request'].path}")
        # APIException already handles the response if it's caught by DRF's handler.
        # But we ensure it has a consistent structure.
        if response is None:
            response = Response({"error": exc.detail, "code": exc.default_code}, status=exc.status_code)

    # For unexpected server errors (500), we want to log the full traceback
    if response is None:
        logger.error(
            f"Admin System Error: {str(exc)}\n{traceback.format_exc()} | User: {context['request'].user} | Path: {context['request'].path}"
        )
        response = Response(
            {
                "error": "A critical system error occurred. Please contact the technical team.",
                "code": "internal_server_error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Normalize DRF's 'detail' key to 'error' for consistency in our admin API
    if response is not None and isinstance(response.data, dict):
        if "detail" in response.data and "error" not in response.data:
            response.data["error"] = response.data.pop("detail")

        # Add a unique Request ID to the response for tracking
        request_id = getattr(context["request"], "request_id", "N/A")
        response.data["request_id"] = request_id

    return response
