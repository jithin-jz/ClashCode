from django.apps import AppConfig


class GithubSyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "github"
    verbose_name = "GitHub Sync"

    def ready(self):
        import github.signals  # noqa: F401
