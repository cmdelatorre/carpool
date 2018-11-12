from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from trips.models import Trip


@receiver(m2m_changed, sender=Trip.passengers.through, dispatch_uid='compute_trip_price')
def compute_trip_price(sender, instance, action, reverse, model, pk_set, using, **kwargs):
    """Whenever the passengers of a Trip change, the price_per_trip must be recomputed."""
    
    if action.startswith('post_'):
        instance.set_price_per_passenger()
