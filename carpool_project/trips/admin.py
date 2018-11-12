from collections import defaultdict
from decimal import Decimal
from django.contrib import admin
from django.http import HttpResponse

from trips.models import Car, Trip

admin.site.register(Car)


def compute_payments(queryset):
    
    # payments: dict in which each key is a pair: 
    #   (passenger, car) 
    # and the value adds the prices of all the trips in which the passenger traveled in that car
    #   (passenger, car): Total payment of passenger to the car owner
    payments = defaultdict(Decimal)

    # explain: dict in which each key is a pair: 
    #   (passenger, car) 
    # and the value includes tuples (date, way) for all the trips of the passenger in that car
    #   (passenger, car): details of trips for the passenger in the car

    explain =  defaultdict(list)

    def do_explain(trip):
        return "{} ({})".format(trip[DATE], trip[WAY])

    for trip in queryset:
        for passenger in trip.passengers.exclude(id=trip.car.owner.id):
            key = (passenger.username, trip.car.owner.username)
            payments[key] += trip.price_per_passenger
            explain[key].append(f"{trip.TRIP_WAYS[trip.way]} el {str(trip.date)}")
    
    text = "\n".join(
        f"{k[0]} paga a {k[1]}: {payments[k]} por {explain[k]}" for k in sorted(payments)
    )
    
    return HttpResponse(text, content_type="text/plain")


class TripAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    readonly_fields = ("price_per_passenger",)
    list_display = ('__str__', 'price_per_passenger', 'people_names')
    list_filter = ('car', 'way')
    # fields = ['pub_date', 'question_text']
    actions = ('pay', )

    def pay(self, request, queryset):
        return compute_payments(queryset)
    pay.short_description = "Compute payments"



admin.site.register(Trip, TripAdmin)
