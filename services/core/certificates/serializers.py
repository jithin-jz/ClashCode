from rest_framework import serializers

from .models import CertificateVerificationLog, UserCertificate


class UserCertificateSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for UserCertificate model.
    """

    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()
    verification_url = serializers.CharField(read_only=True)
    certificate_url = serializers.ImageField(source="certificate_image", read_only=True)

    class Meta:
        model = UserCertificate
        fields = [
            "certificate_id",
            "username",
            "full_name",
            "issued_date",
            "is_valid",
            "completion_count",
            "verification_url",
            "certificate_url",
        ]
        read_only_fields = ["certificate_id", "issued_date", "completion_count"]

    def get_full_name(self, obj):
        user = obj.user
        return f"{user.first_name} {user.last_name}".strip() or user.username


class CertificateEligibilitySerializer(serializers.Serializer):
    """
    Serializer for checking certificate eligibility.
    """

    eligible = serializers.BooleanField()
    completed_challenges = serializers.IntegerField()
    required_challenges = serializers.IntegerField()
    has_certificate = serializers.BooleanField()
    remaining_challenges = serializers.IntegerField()


class CertificateVerificationSerializer(serializers.Serializer):
    """
    Serializer for certificate verification responses.
    """

    valid = serializers.BooleanField()
    certificate = UserCertificateSerializer(allow_null=True)


class CertificateVerificationLogSerializer(serializers.ModelSerializer):
    """
    Serializer for auditing verification logs.
    """

    class Meta:
        model = CertificateVerificationLog
        fields = ["verified_at", "ip_address", "user_agent", "referer"]
        read_only_fields = fields
