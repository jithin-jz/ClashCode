import logging

from django.contrib.auth.models import User
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from posts.models import Post
from users.models import UserFollow

from .services import NotificationService

logger = logging.getLogger(__name__)


@receiver(
    m2m_changed,
    sender=Post.likes.through,
    dispatch_uid="create_like_notification_signal",
)
def create_like_notification(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        for user_id in pk_set:
            try:
                actor = User.objects.get(pk=user_id)
                # Don't notify if user likes their own post
                if actor != instance.user:
                    NotificationService.create_notification(
                        recipient=instance.user,
                        actor=actor,
                        verb="liked your post",
                        target=instance,
                        push_title="New Like!",
                        push_body=f"{actor.username} liked your post: {instance.caption[:30]}...",
                    )
            except User.DoesNotExist:
                continue


@receiver(post_save, sender=UserFollow, dispatch_uid="create_follow_notification_signal")
def create_follow_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_notification(
            recipient=instance.following,
            actor=instance.follower,
            verb="started following you",
            target=instance.following,
            push_title="New Follower!",
            push_body=f"{instance.follower.username} started following you.",
        )
