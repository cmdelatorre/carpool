from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib import admin
from django.contrib.admin import AdminSite

from django.template.response import TemplateResponse

from trips.models import Car, Trip
from trips.payments import analyze_trips, resolve_collectors_and_payers, assing_payments

from collections import namedtuple

class TripsAdminSite(AdminSite):
    site_header = "Los pibe' del Norte - Carpooling"
    site_title = "Carpool administration"
    site_url = None


admin_site = TripsAdminSite(name='myadmin')


class CarAdmin(admin.ModelAdmin):
    list_display = ('owner', 'description', 'price_per_trip')


admin_site.register(Car, CarAdmin)


def prepare_report_data(queryset):
    analysis = analyze_trips(queryset)
    collectors, payers, even = resolve_collectors_and_payers(analysis["balance"], analysis["index"])
    payments = assing_payments(collectors, payers)
    fn = lambda u: User.objects.get(pk=u).get_full_name()  # Full name
    inject_name = lambda t: (fn(t.id), t.ammount)

    return {
        "details": analysis["details"],
        "payments": {fn(u): map(inject_name, transactions) for u, transactions in payments.items()},
        "even": list(map(inject_name, even))
    }


def compute_payments(request, queryset):
    report_data = prepare_report_data(queryset)
    ordered = queryset.order_by("date")
    report_data.update({
        "date_from": ordered.first().date,
        "date_to": ordered.last().date,
    })

    return TemplateResponse(
        request,
        'trips/report.html',
        report_data
    )


class TripAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    readonly_fields = ("price_per_passenger",)
    list_display = ('date', 'way', 'car', 'price_per_passenger', 'people_names', 'notes')
    list_filter = ('car', 'way')
    ordering = ('-date', 'way')
    actions = ('pay', )

    def pay(self, request, queryset):
        return compute_payments(request, queryset)
    pay.short_description = "Compute payments"



admin_site.register(Trip, TripAdmin)

# This is the default Django Contrib Admin user / group object
# Add this if you need to edit the users / groups in your custom admin
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)
