from django.contrib import admin

from .models import CertificateVerificationLog, UserCertificate


@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "certificate_id",
        "issued_date",
        "is_valid",
        "completion_count",
    )
    search_fields = ("user__username", "user__email", "certificate_id")
    list_filter = ("is_valid", "issued_date")


@admin.register(CertificateVerificationLog)
class CertificateVerificationLogAdmin(admin.ModelAdmin):
    list_display = ("certificate", "verified_at", "ip_address", "user_agent")
    list_filter = ("verified_at",)
    search_fields = ("certificate__certificate_id", "ip_address")
    readonly_fields = (
        "certificate",
        "verified_at",
        "ip_address",
        "user_agent",
        "referer",
    )
