from .assist_service import AssistService
from .progression_service import ProgressionService
from .submission_service import SubmissionService


class ChallengeService(ProgressionService, SubmissionService, AssistService):
    """
    Unified Challenge Service.
    Provides a clean API for all challenge-related business logic.
    """

    @staticmethod
    def process_submission(user, challenge, passed=False):
        """Backward compatibility wrapper for process_submission_result."""
        return SubmissionService.process_submission_result(user, challenge, passed)

    @staticmethod
    def purchase_ai_assist(user, challenge):
        """Backward compatibility wrapper for purchase_ai_hint."""
        return AssistService.purchase_ai_hint(user, challenge)
