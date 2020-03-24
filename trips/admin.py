from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.html import format_html

from trips.models import Car, Trip, Report


class TripsAdminSite(AdminSite):
    site_header = "Los pibe' del Norte - Carpooling"
    site_title = "Carpool administration"
    site_url = None


admin_site = TripsAdminSite(name="myadmin")


class CarAdmin(admin.ModelAdmin):
    list_display = ("owner", "description", "price_per_trip")


admin_site.register(Car, CarAdmin)

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

class TripInline(admin.TabularInline):
    model = Trip
    extra = 0
    can_delete = False
    show_change_link = True

class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "creator", "created_time", "report_trips_since", "report_trips_until", "people_involved",
        "payments"
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

from django.contrib import messages
from django.http import HttpResponseRedirect


class FilterTripsIfTheyHaveAReport(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'is reported?'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'already_reported'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ("yes", 'Alredy reported'),
            ("no", 'Un-reported'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either True or)
        # to decide how to filter the queryset.
        if self.value() is not None:
            return queryset.filter(report__isnull=(self.value()=="no"))

class TripAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    readonly_fields = ("price_per_passenger",)
    list_display = (
        "date", "way", "car", "price_per_passenger", "people_names", "included_in_report", "notes"
    )
    list_filter = ("car", "way", FilterTripsIfTheyHaveAReport)
    ordering = ("-date", "way")
    actions = ("create_report", )

    def included_in_report(self, obj):
        if obj.report is not None:
            return format_html(f"<a href='{obj.report.get_absolute_url()}''>{obj.report}</a>")
        else:
            return None
    included_in_report.allow_tags = True

    def create_report(self, request, queryset):
        already_on_report = queryset.filter(report__isnull=False)
        if already_on_report.exists():
            self.message_user(
                request,
                "These trips are already on a report: %s" % str(already_on_report),
                level=messages.WARNING)
            return

        report = Report.objects.create(creator=request.user)
        queryset.update(report=report)
        self.message_user(request, "New report created: %s" % str(report))
        return HttpResponseRedirect(reverse("trips:report_payments", args=(report.id,)))

    create_report.short_description = "Create a report with the selected trips"

admin_site.register(Trip, TripAdmin)


# This is the default Django Contrib Admin user / group object
# Add this if you need to edit the users / groups in your custom admin
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)
