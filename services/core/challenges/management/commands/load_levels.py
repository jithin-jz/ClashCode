"""
Django Management Command: Load Levels
Loads global challenges from markdown files in challenges/content/ into the database.
"""

import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from challenges.models import Challenge


class Command(BaseCommand):
    help = "Load levels from challenges/content/ markdown files into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing global challenges before loading",
        )

    def parse_markdown_level(self, filepath):
        """
        Parses a markdown file with YAML-like frontmatter.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract frontmatter
        fm_match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if not fm_match:
            return None

        fm_text = fm_match.group(1)
        body = content[fm_match.end() :].strip()

        # Simple frontmatter parser (key: value)
        data = {}
        for line in fm_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Type conversion
                if value.isdigit():
                    value = int(value)
                data[key] = value

        # Extract Initial Code and Test Code from body
        # They are at the end in ```python ... ``` blocks

        # Initial Code
        initial_match = re.search(r"### Initial Code\n```python\n(.*?)\n```", body, re.DOTALL)
        if initial_match:
            data["initial_code"] = initial_match.group(1)
            # Remove from body to get description
            body = body.replace(initial_match.group(0), "").strip()

        # Test Code
        test_match = re.search(r"### Test Code\n```python\n(.*?)\n```", body, re.DOTALL)
        if test_match:
            data["test_code"] = test_match.group(1)
            body = body.replace(test_match.group(0), "").strip()

        data["description"] = body
        return data

    def handle(self, *args, **options):
        content_dir = os.path.join(settings.BASE_DIR, "challenges", "content")
        if not os.path.exists(content_dir):
            self.stdout.write(self.style.ERROR(f"Content directory not found: {content_dir}"))
            return

        level_files = sorted([f for f in os.listdir(content_dir) if f.endswith(".md")])
        levels_data = []
        for filename in level_files:
            data = self.parse_markdown_level(os.path.join(content_dir, filename))
            if data:
                levels_data.append(data)

        target_orders = {level["order"] for level in levels_data}

        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing global challenges..."))
            deleted = Challenge.objects.filter(created_for_user__isnull=True).delete()
            self.stdout.write(self.style.SUCCESS(f"  ✓ Deleted {deleted[0]} challenges"))
        else:
            stale_qs = Challenge.objects.filter(created_for_user__isnull=True).exclude(order__in=target_orders)
            stale_count = stale_qs.count()
            if stale_count:
                stale_qs.delete()
                self.stdout.write(self.style.WARNING(f"Removed {stale_count} stale challenges"))

        self.stdout.write(self.style.HTTP_INFO(f"Loading {len(levels_data)} levels from content/"))

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for level in levels_data:
                order = level["order"]
                challenge, created = Challenge.objects.update_or_create(
                    created_for_user=None,
                    order=order,
                    defaults={
                        "title": level["title"],
                        "slug": level["slug"],
                        "description": level["description"],
                        "initial_code": level["initial_code"],
                        "test_code": level["test_code"],
                        "xp_reward": level["xp_reward"],
                        "target_time_seconds": level["target_time_seconds"],
                    },
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {challenge.title}"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"  ↻ Updated: {challenge.title}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {created_count + updated_count} challenges."))
