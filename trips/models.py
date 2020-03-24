import logging
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.utils.timezone import now
from django.urls import reverse

from trips.payments import prepare_report_data


logger = logging.getLogger(__name__)

DESCRIPTION_MAX = 2048


class Car(models.Model):
    description = models.CharField(max_length=DESCRIPTION_MAX, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="cars",
    )
    price_per_trip = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, blank=True
    )  # Up to $99.999,99

    def __str__(self):
        return f"Auto de {self.owner.username.capitalize()}"


from django.core.exceptions import FieldError

class Trip(models.Model):
    GOTO = "go_to"
    RETURN = "return"
    TRIP_WAYS = {GOTO: "Ida", RETURN: "Vuelta"}
    date = models.DateField(default=now)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="trips")
    way = models.CharField(max_length=8, choices=TRIP_WAYS.items(), default=GOTO)
    passengers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="trips")
    price_per_passenger = models.DecimalField(
        max_digits=5, decimal_places=2, null=True
    )  # Up to $99.999,99
    notes = models.CharField(max_length=DESCRIPTION_MAX, blank=True)
    report = models.ForeignKey(
        "trips.Report",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trips"
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=["date", "car", "way"], name='unique_daily_trip_per_way_car'),
        ]

    def get_absolute_url(self):
        return reverse('admin:trips_trip_change', args=(self.id,))

    def __str__(self):
        return f"{self.date} {Trip.TRIP_WAYS[self.way]} en el {self.car}"

    def save(self, *args, **kwargs):
        """Make sure the report is not changed (once it is set)."""
        if self.pk and self.report:
            report_id = Trip.objects.values('report__id').get(pk=self.pk)['report__id']
            print(report_id)
            if report_id is not None and report_id != self.report.id:
                raise ValueError("Can't change the report of a trip, once set! "
                                 "Delete all the Report if needed.")

        return super().save(*args, **kwargs)  # Call the "real" save() method.

    def set_price_per_passenger(self):
        """Compute the price per passenger of the trip and set on the instance.

        Triggers a self.save()

        """
        pk_set = {p.pk for p in self.passengers.all()}
        n_people = len(pk_set.union({self.car.owner.pk}))
        price_per_passenger = self.car.price_per_trip / n_people
        price_per_passenger = price_per_passenger.quantize(Decimal('0.01'))
        if price_per_passenger != self.price_per_passenger:
            self.price_per_passenger = price_per_passenger
            self.save()
            logger.debug(f"Price per passenger saved for {self}: {price_per_passenger}")

    def people_names(self):
        """CSV string with the passengers and driver's names"""
        return ', '.join(
            {p.first_name for p in self.passengers.all()}.union({self.car.owner.first_name})
        )


class Report(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="reports")
    created_time = models.DateTimeField(auto_now=False, auto_now_add=True)

    def get_absolute_url(self):
        return reverse('admin:trips_report_change', args=(self.id,))

    def __str__(self):
        return f"Report ({self.id or ''}) of {str(self.created_time.date())} by {self.creator}"

    @property
    def payments_report(self):
        report_data = None
        if self.trips.exists():
            report_data = prepare_report_data(self.trips.all())
            ordered = self.trips.order_by("date")
            report_data.update({
                "date_from": ordered.first().date,
                "date_to": ordered.last().date,
            })
        return report_data
