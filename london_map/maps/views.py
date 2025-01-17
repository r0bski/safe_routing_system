from django.shortcuts import render
from .route_builder import calc_route
from geopy.geocoders import Nominatim

def map_view(request):
    return render(request, 'maps/map_view.html')

def about_view(request):
    return render(request, 'maps/about.html')

def get_route(request):
    if request.method == 'POST':
        start = request.POST.get('start')
        destination = request.POST.get('destination')
        
        # Geocode the user inputs
        geolocator = Nominatim(user_agent="my_django_app")
        
        start_location = geolocator.geocode(start)
        destination_location = geolocator.geocode(destination)
        print(start_location)
        # Check if both locations were found
        if not start_location or not destination_location:
            return render(request, 'maps/map_view.html', {
                'message': "Could not geocode one or both of the locations."
            })

        # Extract lat/lon
        start_coords = (start_location.latitude, start_location.longitude)
        dest_coords = (destination_location.latitude, destination_location.longitude)

        # Now run your route logic with these coordinates
        route = calc_route(start_coords, dest_coords)

        return render(request, 'maps/map_view.html', {
            'message': f"Route from {start} to {destination}",
            'route': route,  # if you want to display or map it
        })
    return render(request, 'maps/map_view.html')