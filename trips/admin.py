from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib import admin
from django.contrib.admin import AdminSite

from django.template.response import TemplateResponse

from trips.models import Car, Trip
from trips.payments import create_pay_collect_matrix

from collections import namedtuple

class TripsAdminSite(AdminSite):
    site_header = "Los pibe' del Norte - Carpooling"
    site_title = "Carpool administration"
    site_url = None


admin_site = TripsAdminSite(name='myadmin')


class CarAdmin(admin.ModelAdmin):
    list_display = ('owner', 'description', 'price_per_trip')


admin_site.register(Car, CarAdmin)


def compute_payments(request, queryset):

    payments, details = create_pay_collect_matrix(queryset)

    from_index = {i: person.get_full_name() for i, person in enumerate(User.objects.all())}

    ReportLine = namedtuple("ReportLine", ("person", "action", "from_to", "ammount", "other"))
    report = []
    visited = []
    for row, u in zip(payments, User.objects.all()):
        person = u.get_full_name()
        for i, ammount in enumerate(row):
            other = from_index[i]
            if ammount == 0 or (person, other) in visited or (other, person) in visited:
                continue
            action, from_to = ammount <= 0 and ("paga", "a") or ("cobra", "de")
            report.append(ReportLine(person, action, from_to, round(abs(ammount), 2), other))
            visited.append((person, other))

    return TemplateResponse(request, 'trips/report.html', {"report": report, "details": details})


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
