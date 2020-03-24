from django.contrib.auth import get_user_model
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from trips.models import Trip, Report
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.timezone import datetime
from django.views.generic import DetailView, TemplateView, CreateView, UpdateView
from django.views.generic.edit import ModelFormMixin


class TripForm(ModelForm):
    class Meta:
        model = Trip
        fields = ['date', 'car', 'way']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.fields:
            self.fields[name].widget.attrs['readonly'] = True
            self.fields[name].widget.attrs['style'] = "pointer-events: none;"  # Hack de vago


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
        register_existing = trip.id and reverse("trips:register_existing", args=[trip.id])
        register_new = reverse("trips:register_new")
        context["processing_url"] = register_existing or register_new
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


class ReportPayments(DetailView):
    http_method_names = ['get']
    template_name = "trips/report.html"
    model = Report

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.object.payments_report)
        return context
