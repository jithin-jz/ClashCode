from django.contrib.auth.models import User
from django.utils import timezone

from administration.exceptions import AdminResourceNotFound, AdminValidationError
from administration.models import AdminReport
from administration.utils import log_admin_action


class ReportService:
    @staticmethod
    def list_reports(status_filter=None, priority=None, target_username=None):
        """Lists reports in the queue with filters."""
        qs = AdminReport.objects.select_related("target_user", "created_by", "resolved_by")
        if status_filter:
            qs = qs.filter(status=status_filter.strip().upper())
        if priority:
            qs = qs.filter(priority=priority.strip().upper())
        if target_username:
            qs = qs.filter(target_user__username__icontains=target_username.strip())
        return qs[:100]

    @staticmethod
    def create_report(
        created_by,
        target_username,
        title,
        summary,
        category="GENERAL",
        priority=AdminReport.Priority.MEDIUM,
        context=None,
        request=None,
    ):
        """Creates a new admin report."""
        try:
            target = User.objects.get(username=target_username.strip())
        except User.DoesNotExist:
            raise AdminResourceNotFound("Target user not found.")

        if not title.strip() or not summary.strip():
            raise AdminValidationError("Title and summary are required.")

        report = AdminReport.objects.create(
            target_user=target,
            created_by=created_by,
            title=title.strip(),
            summary=summary.strip(),
            category=category.strip().upper() or "GENERAL",
            priority=priority.strip().upper() or AdminReport.Priority.MEDIUM,
            context=context or {},
        )

        log_admin_action(
            admin=created_by,
            action="CREATE_ADMIN_REPORT",
            target_user=target,
            request=request,
            details={"report_id": report.id, "priority": report.priority},
        )
        return report

    @staticmethod
    def update_report(admin, report_id, updates, request=None):
        """Updates a report queue item."""
        report = AdminReport.objects.select_related("target_user").filter(id=report_id).first()
        if not report:
            raise AdminResourceNotFound("Report not found.")

        if "status" in updates:
            report.status = updates["status"]
            if report.status == AdminReport.Status.RESOLVED:
                report.resolved_at = timezone.now()
                report.resolved_by = admin
        if "priority" in updates:
            report.priority = updates["priority"]
        if "summary" in updates:
            report.summary = updates["summary"]

        report.save()

        log_admin_action(
            admin=admin,
            action="UPDATE_ADMIN_REPORT",
            target_user=report.target_user,
            request=request,
            details={
                "report_id": report.id,
                "status": report.status,
                "priority": report.priority,
            },
        )
        return report
