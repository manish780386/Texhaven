class SecurityHeadersMiddleware:
    """Strict headers for the JSON API (the admin and docs keep Django's defaults)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/v1/"):
            response["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
            response["Cache-Control"] = "no-store"
            response["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
            response["Cross-Origin-Resource-Policy"] = "same-site"
        return response
