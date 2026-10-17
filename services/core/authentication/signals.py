from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .revocation import set_user_disabled


@receiver(pre_save, sender=User)
def remember_active_state(sender, instance, **kwargs):
    _ = sender, kwargs
    if instance.pk:
        instance._was_active = User.objects.filter(pk=instance.pk).values_list("is_active", flat=True).first()
    else:
        instance._was_active = None


@receiver(post_save, sender=User)
def mirror_account_status(sender, instance, created, **kwargs):
    """Tell other services (chat) when an account is disabled or re-enabled."""
    _ = sender, kwargs
    was_active = getattr(instance, "_was_active", None)
    if created:
        if not instance.is_active:
            set_user_disabled(instance.pk, True)
        return
    if was_active is not None and was_active != instance.is_active:
        set_user_disabled(instance.pk, not instance.is_active)
