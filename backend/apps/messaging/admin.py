from django.contrib import admin, messages

from .models import AbuseReport, AuditLog, Blocklist, Message, WaitlistEntry
from .services import block_number


class ReadOnly(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Message)
class MessageAdmin(ReadOnly):
    """Encrypted fields are hidden on purpose. Use `manage.py reveal_message` for legal requests."""

    list_display = ("track_id", "status", "to_masked", "to_country", "segments", "risk_score", "created_at")
    list_filter = ("status", "to_country")
    search_fields = ("track_id",)
    exclude = ("to_enc", "body_enc", "to_hash", "sender_ip_hash", "optout_token")
    actions = ["block_recipient"]

    @admin.action(description="Block recipient of selected messages")
    def block_recipient(self, request, queryset):
        n = sum(block_number(m.to_hash, "admin") for m in queryset)
        self.message_user(request, f"{n} number(s) blocked.", messages.SUCCESS)


@admin.register(AbuseReport)
class AbuseReportAdmin(ReadOnly):
    list_display = ("created_at", "category", "reviewed", "message")
    list_filter = ("category", "reviewed")
    actions = ["mark_reviewed"]

    @admin.action(description="Mark as reviewed")
    def mark_reviewed(self, request, queryset):
        queryset.update(reviewed=True)


@admin.register(Blocklist)
class BlocklistAdmin(admin.ModelAdmin):
    list_display = ("created_at", "source")


@admin.register(AuditLog)
class AuditLogAdmin(ReadOnly):
    list_display = ("created_at", "event", "message_id")
    list_filter = ("event",)


@admin.register(WaitlistEntry)
class WaitlistAdmin(ReadOnly):
    list_display = ("email", "created_at")
