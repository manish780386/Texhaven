from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core import turnstile
from apps.core.net import client_ip

from .engine import scan


class ScanSerializer(serializers.Serializer):
    text = serializers.CharField(min_length=1, max_length=1000, trim_whitespace=True)
    turnstile_token = serializers.CharField(required=False, allow_blank=True, max_length=4096)


class ScanView(APIView):
    """Free scam checker. Nothing is stored."""

    throttle_scope = "scan"

    def post(self, request):
        ser = ScanSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not turnstile.verify(ser.validated_data.get("turnstile_token"), client_ip(request)):
            return Response({"detail": "Bot check failed. Please retry."}, status=status.HTTP_400_BAD_REQUEST)
        result = scan(ser.validated_data["text"])
        return Response(result.as_dict())
