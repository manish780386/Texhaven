from rest_framework import serializers

from .models import AbuseReport


class MessageCreateSerializer(serializers.Serializer):
    to = serializers.CharField(max_length=32)
    body = serializers.CharField(max_length=1000, trim_whitespace=True)
    turnstile_token = serializers.CharField(required=False, allow_blank=True, max_length=4096)


class WaitlistSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    turnstile_token = serializers.CharField(required=False, allow_blank=True, max_length=4096)


class ReportSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=AbuseReport.Category.choices)
    details = serializers.CharField(required=False, allow_blank=True, max_length=500)
    turnstile_token = serializers.CharField(required=False, allow_blank=True, max_length=4096)
