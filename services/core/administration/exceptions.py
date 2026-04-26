from rest_framework import status
from rest_framework.exceptions import APIException


class AdminBaseException(APIException):
    """Base exception for all administration-related errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An administrative error occurred."
    default_code = "admin_error"


class AdminPermissionDenied(AdminBaseException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class AdminResourceNotFound(AdminBaseException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The requested resource was not found."
    default_code = "not_found"


class AdminValidationError(AdminBaseException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid data provided."
    default_code = "validation_error"


class AdminSystemError(AdminBaseException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "A critical system error occurred in the administration module."
    default_code = "system_error"
