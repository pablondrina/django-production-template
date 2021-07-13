from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from project.apps.places.models import Address
from project.utils.geolocation import point_to_address


@receiver(pre_save, sender=Address)
def get_address_from_location(sender, instance, **kwargs):
    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        # Object is new, so field hasn't technically changed, but you may want to do something else here.
        point_to_address(instance.location, instance)
    else:
        if not obj.location == instance.location:
            point_to_address(instance.location, instance)
