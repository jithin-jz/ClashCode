import logging

from celery import shared_task

from ..services import LeaderboardService

logger = logging.getLogger(__name__)


@shared_task
def update_leaderboard_cache():
    """
    Periodic task to calculate and cache the leaderboard.
    """
    logger.info("Starting leaderboard calculation task...")

    try:
        # Force refresh by bypassing cache in build
        data = LeaderboardService.get_leaderboard(use_cache=False)
        logger.info("Leaderboard updated successfully.")
        return {"status": "success", "entries": len(data)}

    except Exception as e:
        logger.exception("Leaderboard task failed: %s", str(e))
        return {"status": "error", "error": str(e)}
