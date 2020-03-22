import logging
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.timezone import now, datetime


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

    class Meta:
        unique_together = ["date", "car", "way"]

    def __str__(self):
        return f"{self.date} {Trip.TRIP_WAYS[self.way]} en el {self.car}"

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
        return ', '.join({p.first_name for p in self.passengers.all()}.union({self.car.owner.first_name}))
