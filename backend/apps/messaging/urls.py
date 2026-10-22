from django.urls import path

from . import views

urlpatterns = [
    path("waitlist/", views.WaitlistView.as_view()),
    path("messages/", views.MessageCreateView.as_view()),
    path("messages/<str:track_id>/", views.MessageDetailView.as_view()),
    path("messages/<str:track_id>/mock-pay/", views.MockPayView.as_view()),
    path("recipient/<str:token>/", views.RecipientView.as_view()),
    path("recipient/<str:token>/block/", views.RecipientBlockView.as_view()),
    path("recipient/<str:token>/report/", views.RecipientReportView.as_view()),
    path("webhooks/stripe/", views.StripeWebhookView.as_view()),
    path("webhooks/twilio/status/", views.TwilioStatusView.as_view()),
    path("webhooks/twilio/inbound/", views.TwilioInboundView.as_view()),
]
