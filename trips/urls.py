from django.contrib.auth.decorators import login_required
from django.urls import path
from trips.views import TripRegistrationConfirmation, RegisterNewTrip, RegisterInExistingTrip, ReportPayments

app_name = 'trips'
urlpatterns = [
    path(
        'register/riding_with/<str:username>/',
        login_required(TripRegistrationConfirmation.as_view()),
        name="confirm",
    ),
    path(
        'register/new/',
        login_required(RegisterNewTrip.as_view()),
        name="register_new",
    ),
    path(
        'register/<int:pk>/',
        login_required(RegisterInExistingTrip.as_view()),
        name="register_existing",
    ),

    path(
        'report/<int:pk>/',
        login_required(ReportPayments.as_view()),
        name="report_payments",
    ),
]
