import random
import pandas as pd
from django.core.management.base import BaseCommand
from api.models import FuelStop  # Replace `api` with your app name if needed

class Command(BaseCommand):
    help = "Load fuel stop data from an Excel file and populate the database with random coordinates"

    def handle(self, *args, **kwargs):
        file_path = r"C:\Users\Moaz Tarek\Downloads\fuel-prices-for-be-assessment.xlsx"
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            latitude, longitude = self.random_coordinates()
            FuelStop.objects.create(
                name=row['Truckstop Name'],
                address=row['Address'],
                city=row['City'],
                state=row['State'],
                latitude=latitude,
                longitude=longitude,
                price_per_gallon=row['Retail Price']
            )

        self.stdout.write(self.style.SUCCESS("Fuel data loaded successfully!"))

    @staticmethod
    def random_coordinates():
        """
        Generate random coordinates within the USA.
        """
        latitude = random.uniform(24.396308, 49.384358)  # USA Latitude Range
        longitude = random.uniform(-125.0, -66.93457)   # USA Longitude Range
        return latitude, longitude
