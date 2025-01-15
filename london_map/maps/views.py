from django.shortcuts import render

def map_view(request):
    return render(request, 'maps/map_view.html')

def get_route(request):
    if request.method == 'POST':
        start = request.POST.get('start')
        destination = request.POST.get('destination')
        # Perform your safe-route logic here
        # ...
        return render(request, 'maps/map_view.html', {
            'message': f"Received start={start}, destination={destination}"
        })
    return render(request, 'maps/map_view.html')