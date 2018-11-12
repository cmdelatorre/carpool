from django.apps import AppConfig


class TripsConfig(AppConfig):
    name = "trips"

    def ready(self):
        import trips.signals
