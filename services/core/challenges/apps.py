import importlib

from django.apps import AppConfig


class ChallengesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "challenges"

    def ready(self):
        importlib.import_module("challenges.signals")
