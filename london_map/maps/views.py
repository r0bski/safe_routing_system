from django.shortcuts import render
from .route_builder import calc_route
from .route_builder import is_in_london
from .crime_analytics import crime_heatmap
from .crime_analytics import crime_counts
from .crime_analytics import generate_temporal_plot
from .route_builder import clear_map_from_memory
from geopy.geocoders import Nominatim
import json

DEBUG = True


def map_view(request):
    return render(request, "maps/map_view.html")


def get_route(request):
    if request.method == "POST":
        # Get start and destination
        start = request.POST.get("start")
        destination = request.POST.get("destination")

        start = start + ", London"
        destination = destination + ", London"

        # Get exact address of locations
        geolocator = Nominatim(user_agent="my_django_app")
        start_location = geolocator.geocode(start)
        destination_location = geolocator.geocode(destination)

        if not start_location or not destination_location:
            return render(request, "maps/map_view.html", {
                "message": "Could not geocode one or both of the locations."
            })

        # Convert to coordinates
        start_coords = (start_location.latitude, start_location.longitude)
        dest_coords = (destination_location.latitude, destination_location.longitude)


        # Check if they are within London
        if not is_in_london(*start_coords):
            return render(request, "maps/map_view.html", {
                "message": f"Your start location '{start}' is outside of London."
            })
        if not is_in_london(*dest_coords):
            return render(request, "maps/map_view.html", {
                "message": f"Your destination '{destination}' is outside of London."
            })

        # Calculate the safest and shortest route
        (safe_route_coords, 
         shortest_route_coords,
         balanced_route_coords, 
         safe_len, 
         short_len,
         balanced_len,
         safe_perctent,
         balanced_percent) = calc_route(start_coords, dest_coords)  

        safe_route_json = json.dumps(safe_route_coords)
        shortest_route_json = json.dumps(shortest_route_coords)
        balanced_route_json = json.dumps(balanced_route_coords)

        return render(request, "maps/map_view.html", {
            "message": f"Route from {start} to {destination}",
            "safe_route_json": safe_route_json,
            "shortest_route_json": shortest_route_json,
            "balanced_route_json": balanced_route_json,
            "safe_len": safe_len,
            "short_len": short_len,
            "balanced_len": balanced_len,
            "safe_perctent": safe_perctent,
            "balanced_percent": balanced_percent
        })

    return render(request, "maps/map_view.html")


def about_view(request):
    global DEBUG
    clear_map_from_memory(DEBUG)
    crime_dict = crime_counts()
    crime_json = json.dumps(crime_dict)
    return render(request, "maps/about.html",{
        "crime_json": crime_json
    })


def heatmap_view(request):
    global DEBUG
    clear_map_from_memory(DEBUG)
    heat_data = crime_heatmap()
    heat_json = json.dumps(heat_data)

    return render(request, "maps/crime_heatmap.html", {
        "heat_json": heat_json
    })

def temporal_view(request):
    global DEBUG
    clear_map_from_memory(DEBUG)
    crime_types = [
        "All Crimes",
        "Violence and sexual offences",
        "Other theft",
        "Anti-social behaviour",
        "Criminal damage and arson",
        "Drugs",
        "Public order",
        "Robbery",
        "Vehicle crime",
        "Other crime",
        "Burglary",
        "Possession of weapons",
        "Theft from the person",
        "Bicycle theft",
        "Shoplifting"
    ]

    # Get filter from request
    filter_str = request.GET.get("filter", "All Crimes")

    # Generate the filterd data
    line_data = generate_temporal_plot(filter_str)
    line_json = json.dumps(line_data)

    # Render template
    return render(request, "maps/temporal_analysis.html", {
        "crime_types": crime_types,
        "selected_type": filter_str,
        "line_json": line_json
    })