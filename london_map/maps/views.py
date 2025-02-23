from django.shortcuts import render
from .route_builder import calc_route
from geopy.geocoders import Nominatim
import json

def map_view(request):
    return render(request, 'maps/map_view.html')

def about_view(request):
    return render(request, 'maps/about.html')

def get_route(request):
    if request.method == 'POST':
        # Get start and destination
        start = request.POST.get('start')
        destination = request.POST.get('destination')

        # Get exact address of locations
        geolocator = Nominatim(user_agent="my_django_app")
        start_location = geolocator.geocode(start)
        destination_location = geolocator.geocode(destination)

        if not start_location or not destination_location:
            return render(request, 'maps/map_view.html', {
                'message': "Could not geocode one or both of the locations."
            })

        # Convert to coordinates
        start_coords = (start_location.latitude, start_location.longitude)
        dest_coords = (destination_location.latitude, destination_location.longitude)

        # Calculate the safest and shortest route
        (safe_route_coords, 
         shortest_route_coords,
         balanced_route_coords, 
         safe_len, 
         short_len,
         balanced_len) = calc_route(start_coords, dest_coords)  

        safe_route_json = json.dumps(safe_route_coords)
        shortest_route_json = json.dumps(shortest_route_coords)
        balanced_route_json = json.dumps(balanced_route_coords)

        return render(request, 'maps/map_view.html', {
            'message': f"Route from {start} to {destination}",
            'safe_route_json': safe_route_json,
            'shortest_route_json': shortest_route_json,
            'balanced_route_json': balanced_route_json,
            'safe_len': safe_len,
            'short_len': short_len,
            'balanced_len': balanced_len
        })

    return render(request, 'maps/map_view.html')


def crime_view(request):
    #TODO...
    return render(request, 'maps/crime_locations.html')