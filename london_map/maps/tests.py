from django.urls import reverse, resolve
from django.test import TestCase
from maps.views import *

class UrlsTest(TestCase):
    def test_map_view_url(self):
        url = reverse('map_view')
        self.assertEqual(resolve(url).func, map_view)

    def test_about_view_url(self):
        url = reverse('about')
        self.assertEqual(resolve(url).func, about_view)

    def test_heatmap_view_url(self):
        url = reverse('crime_heatmap')
        self.assertEqual(resolve(url).func, heatmap_view)
    
    def test_temporal_view_url(self):
        url = reverse('temporal_analysis')
        self.assertEqual(resolve(url).func, temporal_view)

class RouteFinderViewTest(TestCase):
    def test_route_view_no_params(self):
        response = self.client.get(reverse('get_route'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'maps/map_view.html')