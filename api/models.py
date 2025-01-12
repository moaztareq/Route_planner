from django.db import models


class FuelStop(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    price_per_gallon = models.FloatField()

    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"