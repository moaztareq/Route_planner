from django.urls import path
from api.views import find_route_with_fuel_stops, upload_fuel_data

urlpatterns = [
    path('route/', find_route_with_fuel_stops, name='route'),
    path('upload-fuel-data/', upload_fuel_data, name='upload_fuel_data'),
]