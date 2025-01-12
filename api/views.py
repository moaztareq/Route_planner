from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from geopy.distance import geodesic
from api.models import FuelStop
import openrouteservice
import pandas as pd
import random
import os


def find_route_with_fuel_stops(request):
    """
    API endpoint that calculates the optimal fuel stops along a route.
    """
    start = request.GET.get('start')  # Format: "longitude,latitude"
    end = request.GET.get('end')      # Format: "longitude,latitude"
    api_key = request.GET.get('api_key')  # API key from query parameter

    if not start or not end or not api_key:
        return JsonResponse({"error": "Start, end, and API key are required"}, status=400)

    # Step 1: Get the route from the map API
    route = get_route_from_map_api(start, end, api_key)
    if not route:
        return JsonResponse({"error": "Unable to retrieve route"}, status=500)

    # Step 2: Extract route coordinates
    route_coordinates = extract_route_coordinates(route)

    # Step 3: Find optimal fuel stops along the route
    optimal_stops, total_cost = calculate_optimal_fuel_stops(route_coordinates)

    # Step 4: Return response with route, stops, and total cost
    return JsonResponse({
        "route": route,
        "optimal_fuel_stops": optimal_stops,
        "total_fuel_cost": total_cost
    })


def get_route_from_map_api(start, end, api_key):
    """
    Fetches the route from OpenRouteService API using the provided API key.
    """
    client = openrouteservice.Client(key=api_key)

    try:
        # Convert start and end to tuples of (longitude, latitude)
        start_coords = tuple(map(float, start.split(",")))
        end_coords = tuple(map(float, end.split(",")))

        # Fetch the directions
        route = client.directions(
            coordinates=[start_coords, end_coords],
            profile="driving-car",
            format="geojson"
        )
        return route
    except Exception as e:
        print(f"Error fetching route: {e}")
        return None


def extract_route_coordinates(route):
    """
    Extracts the list of coordinates along the route from the GeoJSON response.
    """
    coordinates = route["features"][0]["geometry"]["coordinates"]
    return [(coord[1], coord[0]) for coord in coordinates]  # Convert to (latitude, longitude)


def calculate_optimal_fuel_stops(route_coordinates):
    """
    Calculates the optimal fuel stops along the route.
    """
    max_range = 500  # Maximum range of the vehicle in miles
    mpg = 10  # Miles per gallon
    fuel_capacity = max_range / mpg  # Gallons per tank
    total_cost = 0
    stops = []

    remaining_range = max_range  # Start with a full tank

    for i in range(len(route_coordinates) - 1):
        current_point = route_coordinates[i]
        next_point = route_coordinates[i + 1]
        distance_to_next = geodesic(current_point, next_point).miles

        if remaining_range < distance_to_next:
            # Find the cheapest fuel stop within range
            stop = find_cheapest_fuel_stop(current_point, max_range)
            if stop:
                cost = fuel_capacity * stop.price_per_gallon
                total_cost += cost
                stops.append({
                    "name": stop.name,
                    "address": stop.address,
                    "city": stop.city,
                    "state": stop.state,
                    "price_per_gallon": stop.price_per_gallon,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude,
                    "cost": cost
                })
                remaining_range = max_range  # Refill the tank

        remaining_range -= distance_to_next  # Deduct the distance traveled

    return stops, total_cost


def find_cheapest_fuel_stop(current_point, max_range):
    """
    Finds the cheapest fuel stop within the max range from the current point.
    """
    search_radius = max_range  # Search within the vehicle's range
    nearby_stops = []

    for stop in FuelStop.objects.all():
        stop_coords = (stop.latitude, stop.longitude)
        distance = geodesic(current_point, stop_coords).miles
        if distance <= search_radius:
            nearby_stops.append(stop)

    # Return the cheapest stop or None if no stops are nearby
    return min(nearby_stops, key=lambda x: x.price_per_gallon, default=None)


@csrf_exempt
def upload_fuel_data(request):
    """
    API endpoint to upload an Excel file with fuel stop data and save it to the database.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)

    if not request.FILES.get('file'):
        return JsonResponse({"error": "No file uploaded"}, status=400)

    # Save the uploaded file
    file = request.FILES['file']
    file_path = default_storage.save(f"uploads/{file.name}", file)

    try:
        # Load the Excel file
        df = pd.read_excel(file_path)

        # Save data to the database with random coordinates
        for _, row in df.iterrows():
            latitude, longitude = random_coordinates()
            FuelStop.objects.create(
                name=row['Truckstop Name'],
                address=row['Address'],
                city=row['City'],
                state=row['State'],
                latitude=latitude,
                longitude=longitude,
                price_per_gallon=row['Retail Price']
            )

        # Remove the uploaded file after processing
        os.remove(file_path)

        return JsonResponse({"message": "Fuel data uploaded successfully"}, status=201)
    except Exception as e:
        print(f"Error processing file: {e}")
        return JsonResponse({"error": "Failed to process the uploaded file"}, status=500)


def random_coordinates():
    """
    Generate random coordinates within the USA.
    """
    latitude = random.uniform(24.396308, 49.384358)  # USA Latitude Range
    longitude = random.uniform(-125.0, -66.93457)   # USA Longitude Range
    return latitude, longitude