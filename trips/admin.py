from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse

from trips.models import Car, Trip,Report


class TripsAdminSite(AdminSite):
    site_header = "Los pibe' del Norte - Carpooling"
    site_title = "Carpool administration"
    site_url = None


admin_site = TripsAdminSite(name="myadmin")


class CarAdmin(admin.ModelAdmin):
    list_display = ("owner", "description", "price_per_trip")


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
        "trips/report.html",
        report_data
    )


# def create_report(request, queryset):
#     report = 4
#     v = createReportView()
#     v.object = report
#     response = v.as_view()(request)
#     return TemplateResponse(
#         request,
#         "trips/create_report.html",
#         queryset
#     )
from django.urls import reverse
from django.utils.html import format_html


class TripInline(admin.TabularInline):
    model = Trip
    extra = 0
    can_delete = False
    show_change_link = True

class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "creator", "created_time", "report_trips_since", "report_trips_until", "people_involved", "payments"
    )
    inlines = [TripInline, ]

    def payments(self, obj):
        url = reverse("trips:report_payments", args=(obj.id,))
        return format_html(f"<a href='{url}''>Payments report</a>")
    payments.allow_tags = True
    payments.short_description = "Payments details"

    def report_trips_since(self, obj):
        if obj.trips.exists():
            return obj.trips.order_by("date").first().date

    def report_trips_until(self, obj):
        if obj.trips.exists():
            return obj.trips.order_by("date").last().date

    def people_involved(self, obj):
        people = set()
        if obj.trips.exists():
            passengers = User.objects.filter(trips__in=obj.trips.all()).distinct()
            drivers = {t.car.owner for t in obj.trips.all().distinct()}
            people = drivers.union(passengers)
        return [p.first_name for p in people]



admin_site.register(Report, ReportAdmin)


class TripAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    readonly_fields = ("price_per_passenger",)
    list_display = ("date", "way", "car", "price_per_passenger", "people_names", "included_in_report", "notes")
    list_filter = ("car", "way")
    ordering = ("-date", "way")
    actions = ("pay", )

    def pay(self, request, queryset):
        return compute_payments(request, queryset)
    pay.short_description = "Compute payments"

    def included_in_report(self, obj):
        if obj.report is not None:
            return format_html(f"<a href='{obj.report.get_absolute_url()}''>{obj.report}</a>")
        else:
            return None
    included_in_report.allow_tags = True



admin_site.register(Trip, TripAdmin)

# This is the default Django Contrib Admin user / group object
# Add this if you need to edit the users / groups in your custom admin
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)
