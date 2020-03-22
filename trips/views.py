from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import datetime
from django.views.generic import TemplateView

from trips.models import Trip


class RegisterTrip(TemplateView):
    http_method_names = ['get']
    template_name = "trips/confirm_trip.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        car_owner = get_object_or_404(get_user_model(), username=context["username"])
        d = datetime.now()
        context.update({
            "date": d.date(),
            "way": d.hour <= 12 and Trip.GOTO or Trip.RETURN,
            "passenger": self.request.user,
            "car_owner": car_owner,
        })
        return context

    # def get(self, request, username=None):
