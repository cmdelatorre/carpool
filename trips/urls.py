from django.contrib.auth.decorators import login_required
from django.urls import path
from trips.views import TripRegistrationConfirmation

urlpatterns = [
    path('register/<str:username>/', login_required(TripRegistrationConfirmation.as_view())),
]
