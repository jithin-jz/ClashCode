from django.contrib.auth.models import User
from django.db.models import Avg, Count, Subquery, OuterRef, Q, ExpressionWrapper, DurationField, F
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils import timezone

from challenges.models import UserProgress
from store.models import Purchase
from administration.models import AdminAuditLog, AdminNote, AdminReport
from administration.permissions import can_manage_user
from administration.exceptions import AdminPermissionDenied, AdminResourceNotFound, AdminValidationError

class UserService:
    @staticmethod
    def toggle_user_block(username, admin_user, reason="", request=None):
        """Toggles a user's active status."""
        from administration.utils import log_admin_action # Avoid circular import

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AdminResourceNotFound("User not found")

        allowed, message = can_manage_user(admin_user, user)
        if not allowed:
            raise AdminPermissionDenied(message)

        if user.is_superuser and user.is_active:
            active_superusers = User.objects.filter(is_superuser=True, is_active=True).exclude(id=user.id)
            if not active_superusers.exists():
                raise AdminValidationError("Cannot block the last active superuser account.")

        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        action = "BLOCK_USER" if not user.is_active else "UNBLOCK_USER"
        log_admin_action(
            admin=admin_user,
            action=action,
            target_user=user,
            request=request,
            details={"reason": reason}
        )
        
        status_text = "blocked" if not user.is_active else "unblocked"
        return f"User {user.username} has been {status_text}.", user.is_active

    @staticmethod
    def soft_delete_user(username, admin_user, reason="", request=None):
        """Soft-deletes a user to preserve data integrity while removing PII."""
        from administration.utils import log_admin_action # Avoid circular import

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AdminResourceNotFound("User not found")

        allowed, message = can_manage_user(admin_user, user)
        if not allowed:
            raise AdminPermissionDenied(message)

        if user.is_superuser:
            active_superusers = User.objects.filter(is_superuser=True, is_active=True).exclude(id=user.id)
            if not active_superusers.exists():
                raise AdminValidationError("Cannot delete the last active superuser account.")

        old_username = user.username
        old_email = user.email
        user.username = f"deleted_{user.id}_{timezone.now().timestamp()}"
        user.email = f"deleted_{user.id}@clashcode.internal"
        user.first_name = "Deleted"
        user.last_name = "User"
        user.is_active = False
        user.save()

        if hasattr(user, "profile"):
            user.profile.bio = ""
            user.profile.github_username = None
            user.profile.save()

        log_admin_action(
            admin=admin_user,
            action="SOFT_DELETE_USER",
            request=request,
            target_username=old_username,
            target_email=old_email,
            details={"original_username": old_username, "reason": reason}
        )
        return f"User {old_username} has been soft-deleted."

    @staticmethod
    def list_users(admin_user, filters, page=1, page_size=25):
        """Lists users with filtering and pagination."""
        from users.models import UserFollow
        
        followers_sq = UserFollow.objects.filter(following_id=OuterRef('id')).values('following_id').annotate(c=Count('id')).values('c')
        following_sq = UserFollow.objects.filter(follower_id=OuterRef('id')).values('follower_id').annotate(c=Count('id')).values('c')
        
        users = User.objects.select_related("profile").annotate(
            followers_total=Coalesce(Subquery(followers_sq), 0),
            following_total=Coalesce(Subquery(following_sq), 0),
        )
        
        if not admin_user.is_superuser:
            users = users.filter(is_staff=False, is_superuser=False)

        search = (filters.get("search") or "").strip()
        role = (filters.get("role") or "").strip().lower()
        status_filter = (filters.get("status") or "").strip().lower()

        if search:
            users = users.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        if role == "user":
            users = users.filter(is_staff=False, is_superuser=False)
        elif role == "staff":
            users = users.filter(is_staff=True, is_superuser=False)
        elif role == "superuser":
            users = users.filter(is_superuser=True)

        if status_filter == "active":
            users = users.filter(is_active=True)
        elif status_filter == "blocked":
            users = users.filter(is_active=False)

        users = users.order_by("-date_joined", "id")

        paginator = Paginator(users, page_size)
        page_obj = paginator.get_page(page)
        
        return {
            "count": paginator.count,
            "page": page_obj.number,
            "page_size": page_size,
            "total_pages": paginator.num_pages,
            "results": page_obj.object_list
        }

    @staticmethod
    def get_user_details(admin_user, username):
        """Retrieves detailed admin drill-down for a user."""
        from administration.utils import _role_for_user
        
        try:
            target = User.objects.select_related("profile").get(username=username)
        except User.DoesNotExist:
            raise AdminResourceNotFound("User not found")

        if not admin_user.is_superuser and (target.is_staff or target.is_superuser):
            raise AdminPermissionDenied("Only superusers can inspect staff or superuser accounts.")

        progress_qs = UserProgress.objects.filter(user=target).select_related("challenge")
        completed_qs = progress_qs.filter(status=UserProgress.Status.COMPLETED)
        
        purchases = (
            Purchase.objects.filter(user=target)
            .select_related("item")
            .order_by("-purchased_at")[:8]
        )
        recent_logs = AdminAuditLog.objects.filter(
            Q(target_user=target) | Q(target_username=target.username)
        ).order_by("-timestamp")[:8]
        
        notes = AdminNote.objects.filter(target_user=target).order_by("-created_at")[:8]
        reports = AdminReport.objects.filter(target_user=target).order_by("-created_at")[:8]

        avg_completion_time = (
            completed_qs.exclude(started_at__isnull=True, completed_at__isnull=True)
            .annotate(
                duration=ExpressionWrapper(
                    F("completed_at") - F("started_at"),
                    output_field=DurationField(),
                )
            )
            .aggregate(avg=Avg("duration"))
            .get("avg")
        )
        
        avg_seconds = avg_completion_time.total_seconds() if avg_completion_time is not None else 0

        recent_completions = []
        for row in completed_qs.order_by("-completed_at")[:6]:
            recent_completions.append({
                "challenge": row.challenge.title,
                "stars": row.stars,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
            })

        purchase_rows = [{
            "id": p.item.id,
            "name": p.item.name,
            "category": p.item.category,
            "cost": p.item.cost,
            "purchased_at": p.purchased_at.isoformat(),
        } for p in purchases]

        return {
            "target": target,
            "role": _role_for_user(target),
            "summary": {
                "joined_at": target.date_joined.isoformat(),
                "last_login": target.last_login.isoformat() if target.last_login else None,
                "completed_challenges": completed_qs.count(),
                "unlocked_challenges": progress_qs.exclude(status=UserProgress.Status.LOCKED).count(),
                "total_attempts": progress_qs.count(),
                "avg_completion_time_seconds": avg_seconds,
                "purchase_count": Purchase.objects.filter(user=target).count(),
                "open_reports": AdminReport.objects.filter(target_user=target).exclude(status=AdminReport.Status.RESOLVED).count(),
            },
            "recent_completions": recent_completions,
            "recent_purchases": purchase_rows,
            "notes": notes,
            "reports": reports,
            "audit_logs": recent_logs,
        }

    @staticmethod
    def update_user_role(admin_user, username, new_role, request=None):
        """Updates a user's role (Superuser only)."""
        from administration.utils import log_admin_action, _role_for_user
        
        try:
            target = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AdminResourceNotFound("User not found")

        if new_role not in {"user", "staff", "superuser"}:
            raise AdminValidationError("Invalid role.")

        if admin_user == target:
            raise AdminValidationError("You cannot change your own role from the admin panel.")

        if not admin_user.is_superuser:
            raise AdminPermissionDenied("Only superusers can update user roles.")

        previous_role = _role_for_user(target)
        target.is_superuser = (new_role == "superuser")
        target.is_staff = (new_role in {"staff", "superuser"})
        target.save(update_fields=["is_staff", "is_superuser"])

        log_admin_action(
            admin=admin_user,
            action="UPDATE_USER_ROLE",
            target_user=target,
            request=request,
            details={"before": previous_role, "after": new_role},
        )
        return f"Updated {target.username} role to {new_role}."

    @staticmethod
    def bulk_update_user_status(admin_user, usernames, action, request=None):
        """Performs bulk block/unblock actions."""
        from administration.utils import log_admin_action
        
        changed = []
        skipped = []
        target_state = (action == "unblock")
        
        for user in User.objects.filter(username__in=usernames):
            allowed, message = can_manage_user(admin_user, user)
            if not allowed:
                skipped.append({"username": user.username, "reason": message})
                continue
            
            if user.is_superuser and not target_state:
                active_superusers = User.objects.filter(is_superuser=True, is_active=True).exclude(id=user.id)
                if not active_superusers.exists():
                    skipped.append({"username": user.username, "reason": "Cannot block the last active superuser account."})
                    continue
            
            if user.is_active == target_state:
                skipped.append({"username": user.username, "reason": "No change needed."})
                continue
                
            user.is_active = target_state
            user.save(update_fields=["is_active"])
            changed.append(user.username)
            
            log_admin_action(
                admin=admin_user,
                action="BULK_USER_STATUS_UPDATE",
                target_user=user,
                request=request,
                details={"after": {"is_active": user.is_active}, "bulk_action": action},
            )
        
        return {"updated": changed, "skipped": skipped, "action": action}

    @staticmethod
    def generate_user_export_csv(admin_user, filters):
        """Generates CSV rows for user export."""
        from administration.utils import _role_for_user
        
        users = User.objects.select_related("profile").all().order_by("-date_joined", "id")
        if not admin_user.is_superuser:
            users = users.filter(is_staff=False, is_superuser=False)

        search = (filters.get("search") or "").strip()
        role = (filters.get("role") or "").strip().lower()
        status_filter = (filters.get("status") or "").strip().lower()

        if search:
            users = users.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        if role == "user":
            users = users.filter(is_staff=False, is_superuser=False)
        elif role == "staff":
            users = users.filter(is_staff=True, is_superuser=False)
        elif role == "superuser":
            users = users.filter(is_superuser=True)
            
        if status_filter == "active":
            users = users.filter(is_active=True)
        elif status_filter == "blocked":
            users = users.filter(is_active=False)

        yield "username,email,role,status,xp,joined_at,last_login\n"
        for user in users.iterator(chunk_size=1000):
            xp = getattr(getattr(user, "profile", None), "xp", 0)
            last_login = user.last_login.isoformat() if user.last_login else ""
            yield f"{user.username},{user.email},{_role_for_user(user)},{'active' if user.is_active else 'blocked'},{xp},{user.date_joined.isoformat()},{last_login}\n"

    @staticmethod
    def get_user_notes(username):
        """Retrieves internal admin notes for a user."""
        return AdminNote.objects.filter(target_user__username=username).order_by("-created_at")

    @staticmethod
    def create_user_note(admin_user, username, body, is_pinned=False, request=None):
        """Creates a new internal admin note."""
        from administration.utils import log_admin_action
        
        try:
            target = User.objects.get(username=username)
        except User.DoesNotExist:
            raise AdminResourceNotFound("User not found")

        if not body.strip():
            raise AdminValidationError("Note body is required.")

        note = AdminNote.objects.create(
            admin=admin_user,
            target_user=target,
            body=body,
            is_pinned=is_pinned,
        )
        
        log_admin_action(
            admin=admin_user,
            action="CREATE_ADMIN_NOTE",
            target_user=target,
            request=request,
            details={"note_id": note.id, "is_pinned": note.is_pinned},
        )
        return note
