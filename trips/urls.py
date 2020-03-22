from django.contrib.auth.decorators import login_required
from django.urls import path
from trips.views import RegisterTrip

urlpatterns = [
    path('register/<str:username>/', login_required(RegisterTrip.as_view())),
]
