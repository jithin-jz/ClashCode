"""
Management command to seed default achievements into the database.
Run with: python manage.py seed_achievements
"""

from django.core.management.base import BaseCommand

from achievements.models import Achievement

ACHIEVEMENTS = [
    # Challenge
    {
        "slug": "first-blood",
        "title": "First Blood",
        "description": "Complete your first challenge",
        "icon": "Zap",
        "category": "challenge",
        "xp_reward": 10,
        "order": 1,
        "target_value": 1,  # First challenge completed
    },
    {
        "slug": "rising-coder",
        "title": "Rising Coder",
        "description": "Complete 5 challenges",
        "icon": "TrendingUp",
        "category": "challenge",
        "xp_reward": 25,
        "order": 2,
        "target_value": 5,  # Requires 5 challenges
    },
    {
        "slug": "challenge-veteran",
        "title": "Challenge Veteran",
        "description": "Complete 10 challenges",
        "icon": "Medal",
        "category": "challenge",
        "xp_reward": 50,
        "order": 3,
        "target_value": 10,  # Requires 10 challenges
    },
    {
        "slug": "legend",
        "title": "Legend",
        "description": "Complete 25 challenges",
        "icon": "Crown",
        "category": "challenge",
        "xp_reward": 100,
        "order": 4,
        "target_value": 25,  # Requires 25 challenges
    },
    {
        "slug": "speed-demon",
        "title": "Speed Demon",
        "description": "Solve a challenge in under 2 minutes",
        "icon": "Flame",
        "category": "challenge",
        "xp_reward": 40,
        "order": 5,
        "target_value": 1,  # One speed completion
    },
    {
        "slug": "perfectionist",
        "title": "Perfectionist",
        "description": "Earn 3 stars on a challenge",
        "icon": "Star",
        "category": "challenge",
        "xp_reward": 30,
        "order": 6,
        "target_value": 1,  # One 3-star completion
    },
    # Streak
    {
        "slug": "streak-starter",
        "title": "Streak Starter",
        "description": "Maintain a 3-day login streak",
        "icon": "Calendar",
        "category": "streak",
        "xp_reward": 15,
        "order": 10,
        "target_value": 3,  # Requires 3 consecutive days
    },
    {
        "slug": "streak-master",
        "title": "Streak Master",
        "description": "Maintain a 7-day login streak",
        "icon": "Flame",
        "category": "streak",
        "xp_reward": 60,
        "order": 11,
        "target_value": 7,  # Requires 7 consecutive days
    },
    # Social
    {
        "slug": "socializer",
        "title": "Socializer",
        "description": "Follow your first user",
        "icon": "UserPlus",
        "category": "social",
        "xp_reward": 5,
        "order": 20,
        "target_value": 1,  # First follow
    },
    {
        "slug": "networker",
        "title": "Networker",
        "description": "Follow 10 users",
        "icon": "Users",
        "category": "social",
        "xp_reward": 25,
        "order": 21,
        "target_value": 10,  # Requires 10 follows
    },
]


class Command(BaseCommand):
    help = "Seed default achievements into the database"

    def handle(self, *args, **options):
        created_count = 0
        for data in ACHIEVEMENTS:
            _, created = Achievement.objects.update_or_create(slug=data["slug"], defaults=data)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(ACHIEVEMENTS)} achievements ({created_count} new)"))
