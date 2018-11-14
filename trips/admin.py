from collections import defaultdict
from decimal import Decimal
from django.contrib import admin
from django.contrib.admin import AdminSite

from django.http import HttpResponse

from trips.models import Car, Trip




class TripsAdminSite(AdminSite):
    site_header = "Los pibe' del Norte - Carpooling"
    site_title = "Carpool administration"
    site_url = None


admin_site = TripsAdminSite(name='myadmin')


class CarAdmin(admin.ModelAdmin):
    list_display = ('owner', 'description', 'price_per_trip')


admin_site.register(Car, CarAdmin)



def solve_collectors_and_payers(payments):
    """
    Solve the issue when a person must pay to someone (traveled as passenger) but also collect from 
    the same person (traveled as driver).

    It computes the difference in that case.

    """
    processed = defaultdict(bool)
    for transaction in payments.keys():
        print('orig', transaction, payments[transaction])
        # A transaction is a tuple (A, B) such that person A has to pay to person B
        if processed[transaction]:
            continue   
        processed[transaction] = True

        reverse = tuple(reversed(transaction))
        if reverse in payments:
            processed[reverse] = True  # Flag the reverse transaction so it is NOT processed later
            # x le paga a y pero y también le paga a x
            tmp = payments[transaction]
            payments[transaction] = tmp - payments[reverse]
            payments[reverse] = payments[reverse] - tmp
            print('tr', transaction, payments[transaction])
            print('rev', reverse, payments[reverse])

def create_report(payments, explain):
    def pays_or_collects(transaction):
        return 'paga a' if payments[transaction] > 0 else 'cobra de'

    transactions = [f"{k[0]} {pays_or_collects(k)} {k[1]}: ${abs(payments[k])} por {explain[k]}" for k in sorted(payments)]
    return "\n".join(transactions)

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
            key = (passenger.username.capitalize(), trip.car.owner.username.capitalize())
            payments[key] += trip.price_per_passenger
            explain[key].append(f"{trip.TRIP_WAYS[trip.way]} el {str(trip.date)}")
    
    print(payments)
    solve_collectors_and_payers(payments)
    print(payments)

    text = create_report(payments, explain)
    
    return HttpResponse(text, content_type="text/plain")


class TripAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    readonly_fields = ("price_per_passenger",)
    list_display = ('date', 'way', 'car', 'price_per_passenger', 'people_names', 'notes')
    list_filter = ('car', 'way')
    ordering = ('-date', 'way')
    actions = ('pay', )

    def pay(self, request, queryset):
        return compute_payments(queryset)
    pay.short_description = "Compute payments"



admin_site.register(Trip, TripAdmin)
