from django.urls import reverse, resolve
from django.test import TestCase
from maps.views import *


class UrlsTest(TestCase):
    def test_map_view_url(self):
        url = reverse("map_view")
        self.assertEqual(resolve(url).func, map_view)

    def test_about_view_url(self):
        url = reverse("about")
        self.assertEqual(resolve(url).func, about_view)

    def test_heatmap_view_url(self):
        url = reverse("crime_heatmap")
        self.assertEqual(resolve(url).func, heatmap_view)
    
    def test_temporal_view_url(self):
        url = reverse("temporal_analysis")
        self.assertEqual(resolve(url).func, temporal_view)

class ViewTest(TestCase):
    def test_route_view(self):
        response = self.client.get(reverse("get_route"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "maps/map_view.html")

    def test_temporal_view(self):
        response = self.client.get(reverse("temporal_analysis"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "maps/temporal_analysis.html")
        # Check that "crime_types" exists in the context
        self.assertIn("crime_types", response.context)
        self.assertIsNotNone(response.context["crime_types"])
        self.assertIn("line_json", response.context)
        self.assertIsNotNone(response.context["line_json"])

    def test_heatmap_view(self):
        response = self.client.get(reverse("crime_heatmap"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "maps/crime_heatmap.html")
        self.assertIn("heat_json", response.context)
        self.assertIsNotNone(response.context["heat_json"])
    
    def test_about_view(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "maps/about.html")
        self.assertIn("crime_json", response.context)
        self.assertIsNotNone(response.context["crime_json"])