from .account_service import AccountService
from .oauth_service import OAuthService
from .otp_service import OTPService
from .token_service import TokenService


class AuthService(OAuthService, OTPService, TokenService, AccountService):
    """
    Unified Authentication Service that combines OAuth, OTP, Token, and Account management.
    Inherits from specialized services to maintain a clean code structure while providing
    a single entry point for the application.
    """

    pass
