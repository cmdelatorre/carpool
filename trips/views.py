from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timezone import datetime
from django.views.generic import TemplateView, CreateView, UpdateView
from django.views.generic.edit import ModelFormMixin


from trips.models import Trip

from django.forms import ModelForm

class TripForm(ModelForm):
    class Meta:
        model = Trip
        fields = ['date', 'car', 'way']



class TripRegistrationConfirmation(TemplateView, ModelFormMixin):
    http_method_names = ['get']
    template_name = "trips/confirm_trip.html"
    form_class = TripForm
    model = Trip

    def get_context_data(self, **kwargs):

        car_owner = get_object_or_404(get_user_model(), username=kwargs["username"])
        d = datetime.now()
        # GOTO if it's before noon. RETURN otherwise.
        way = d.hour <= 12 and Trip.GOTO or Trip.RETURN

        trip_params = {
            "date": d.date(),
            "car": car_owner.cars.get(),
            "way": way
        }
        try:
            # The Trip already exists
            trip = Trip.objects.get(**trip_params)
        except Trip.DoesNotExist:
            #  A new Trip instance
            trip = Trip(**trip_params)
        self.object = trip

        context = super().get_context_data(**kwargs)
        context["processing_url"] = (
            trip.id is None and reverse("trips:register_new")
            or reverse("trips:register_existing", args=[trip.id])
        )
        return context


class RegisterNewTrip(CreateView):
    http_method_names = ['post']
    form_class = TripForm
    model = Trip
    success_url = "/admin/trips/trip/"

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        response = super().form_valid(form)  # This step saves the Trip instance
        trip = self.object
        trip.passengers.add(self.request.user, trip.car.owner)
        return response


class RegisterInExistingTrip(UpdateView):
    http_method_names = ['post']
    form_class = TripForm
    model = Trip
    success_url = "/admin/trips/trip/"

    def form_valid(self, form):
        """If the form is valid, don't save the Trip instance, just add a passenger."""
        trip = self.object
        trip.passengers.add(self.request.user, trip.car.owner)
        return HttpResponseRedirect(self.get_success_url())