"""Tests for aggregate module functions."""
from unittest.mock import MagicMock, patch

from happenstance.aggregate import (
    _build_pairings,
    _calculate_distance,
    _cities_match_at_word_boundary,
    _geocode_address,
)


class TestCityMatching:
    """Tests for city matching with word boundaries."""
    
    def test_exact_match(self):
        """Test exact city name match."""
        assert _cities_match_at_word_boundary("troy", "troy") is True
        assert _cities_match_at_word_boundary("albany", "albany") is True
    
    def test_substring_with_space_prefix(self):
        """Test substring match with space prefix (e.g., 'downtown troy')."""
        assert _cities_match_at_word_boundary("downtown troy", "troy") is True
        assert _cities_match_at_word_boundary("troy", "downtown troy") is True
    
    def test_substring_with_space_suffix(self):
        """Test substring match with space suffix (e.g., 'troy downtown')."""
        assert _cities_match_at_word_boundary("troy downtown", "troy") is True
        assert _cities_match_at_word_boundary("troy", "troy downtown") is True
    
    def test_substring_without_word_boundary(self):
        """Test substring matching at word boundaries.
        
        Note: This function considers any word-boundary match as valid.
        For example, "albany" in "new albany" matches because "albany"
        appears after a space. In practice, this is acceptable because:
        1. We're operating within a single region
        2. We don't have both "Albany" and "New Albany" in the same dataset
        3. The primary use case is matching "downtown troy" with "troy"
        """
        # These DO match because they're at word boundaries
        assert _cities_match_at_word_boundary("new albany", "albany") is True
        assert _cities_match_at_word_boundary("albany", "new albany") is True
        assert _cities_match_at_word_boundary("west troy", "troy") is True
        assert _cities_match_at_word_boundary("troy", "west troy") is True
        
        # These don't match because they're not at word boundaries
        # (in middle of a word)
        assert _cities_match_at_word_boundary("troyan", "troy") is False
        assert _cities_match_at_word_boundary("troy", "troyan") is False
    
    def test_no_substring(self):
        """Test that completely different cities don't match."""
        assert _cities_match_at_word_boundary("troy", "albany") is False
        assert _cities_match_at_word_boundary("schenectady", "niskayuna") is False


class TestGeocodeAddress:
    """Tests for Nominatim-based geocoding."""
    
    @patch('happenstance.aggregate.requests.get')
    @patch('happenstance.aggregate.time.sleep')
    def test_geocode_success(self, mock_sleep, mock_get):
        """Test successful geocoding with Nominatim."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "lat": "37.7749",
                "lon": "-122.4194"
            }
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = _geocode_address("Market Street", region="San Francisco")
        
        assert result == (37.7749, -122.4194)
        assert mock_get.call_count == 1
        assert mock_sleep.call_count == 1
        
        # Verify the request was made correctly
        call_args = mock_get.call_args
        assert call_args[1]['params']['q'] == "Market Street, San Francisco"
        assert call_args[1]['params']['format'] == "json"
        assert 'User-Agent' in call_args[1]['headers']
    
    @patch('happenstance.aggregate.requests.get')
    @patch('happenstance.aggregate.time.sleep')
    def test_geocode_empty_address(self, mock_sleep, mock_get):
        """Test geocoding with empty address."""
        result = _geocode_address("", region="San Francisco")
        
        assert result is None
        assert mock_get.call_count == 0
        assert mock_sleep.call_count == 0
    
    @patch('happenstance.aggregate.requests.get')
    @patch('happenstance.aggregate.time.sleep')
    def test_geocode_no_results(self, mock_sleep, mock_get):
        """Test geocoding when Nominatim returns no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = _geocode_address("Invalid Address", region="San Francisco")
        
        assert result is None
    
    @patch('happenstance.aggregate.requests.get')
    @patch('happenstance.aggregate.time.sleep')
    def test_geocode_request_error(self, mock_sleep, mock_get):
        """Test geocoding when request fails."""
        mock_get.side_effect = Exception("Network error")
        
        result = _geocode_address("Market Street", region="San Francisco")
        
        assert result is None


class TestCalculateDistance:
    """Tests for haversine distance calculation."""
    
    def test_distance_same_location(self):
        """Test distance between same coordinates is zero."""
        distance = _calculate_distance(37.7749, -122.4194, 37.7749, -122.4194)
        assert distance < 0.01  # Should be very close to 0
    
    def test_distance_known_locations(self):
        """Test distance between known locations."""
        # San Francisco to Los Angeles (approximately 347 miles)
        sf_lat, sf_lon = 37.7749, -122.4194
        la_lat, la_lon = 34.0522, -118.2437
        
        distance = _calculate_distance(sf_lat, sf_lon, la_lat, la_lon)
        
        # Should be approximately 347 miles (within 10 miles tolerance)
        assert 337 < distance < 357
    
    def test_distance_short_distance(self):
        """Test distance for short distances (walking distance)."""
        # Two points approximately 0.5 miles apart in San Francisco
        lat1, lon1 = 37.7749, -122.4194
        lat2, lon2 = 37.7820, -122.4194
        
        distance = _calculate_distance(lat1, lon1, lat2, lon2)
        
        # Should be less than 1 mile
        assert distance < 1.0
        assert distance > 0


class TestBuildPairings:
    """Tests for building event-restaurant pairings with distance calculation."""
    
    @patch('happenstance.aggregate._geocode_address')
    @patch('happenstance.aggregate._fetch_nearby_restaurants')
    def test_pairings_with_distances(self, mock_fetch_nearby, mock_geocode):
        """Test that pairings include distance when geocoding succeeds."""
        # Mock geocoding to return coordinates
        def geocode_side_effect(address, region="San Francisco"):
            if "Waterfront Stage" in address:
                return (37.7749, -122.4194)  # Event location
            elif "Waterfront" in address:
                return (37.7760, -122.4200)  # Restaurant location (close by)
            return None
        
        mock_geocode.side_effect = geocode_side_effect
        mock_fetch_nearby.return_value = []  # No nearby restaurants
        
        events = [
            {
                "title": "Waterfront Jazz Night",
                "category": "live music",
                "location": "San Francisco Waterfront Stage",
                "url": "https://example.com/jazz",
            }
        ]
        
        restaurants = [
            {
                "name": "Blue Harbor Grill",
                "cuisine": "Seafood",
                "address": "San Francisco Waterfront",
                "url": "https://example.com/blue-harbor",
                "match_reason": "Great before a waterfront concert",
            }
        ]
        
        cfg = {"region": "San Francisco"}
        pairings = _build_pairings(events, restaurants, cfg)
        
        assert len(pairings) == 1
        assert pairings[0]["event"] == "Waterfront Jazz Night"
        assert pairings[0]["restaurant"] == "Blue Harbor Grill"
        assert "distance_miles" in pairings[0]
        # Distance should be small (less than 1 mile)
        assert pairings[0]["distance_miles"] < 1.0
    
    @patch('happenstance.aggregate._geocode_address')
    @patch('happenstance.aggregate._fetch_nearby_restaurants')
    def test_pairings_without_distances_when_geocoding_fails(self, mock_fetch_nearby, mock_geocode):
        """Test that pairings work without distance when geocoding fails."""
        mock_geocode.return_value = None  # Geocoding fails
        mock_fetch_nearby.return_value = []
        
        events = [
            {
                "title": "Waterfront Jazz Night",
                "category": "live music",
                "location": "Unknown Location",
                "url": "https://example.com/jazz",
            }
        ]
        
        restaurants = [
            {
                "name": "Blue Harbor Grill",
                "cuisine": "Seafood",
                "address": "Unknown Address",
                "url": "https://example.com/blue-harbor",
                "match_reason": "Great before a waterfront concert",
            }
        ]
        
        cfg = {"region": "San Francisco"}
        pairings = _build_pairings(events, restaurants, cfg)
        
        assert len(pairings) == 1
        assert pairings[0]["event"] == "Waterfront Jazz Night"
        assert pairings[0]["restaurant"] == "Blue Harbor Grill"
        # Distance should not be present when geocoding fails
        assert "distance_miles" not in pairings[0]
    
    @patch('happenstance.aggregate._geocode_address')
    @patch('happenstance.aggregate._fetch_nearby_restaurants')
    def test_pairings_prioritize_same_city_over_variety(self, mock_fetch_nearby, mock_geocode):
        """Test that same-city restaurants are always preferred over different-city ones.
        
        This is a regression test for the issue where variety penalties could cause
        events to be paired with restaurants in different cities (e.g., Troy Night Out
        being paired with Mario's Pizza in Niskayuna instead of Troy restaurants).
        """
        mock_geocode.return_value = None  # Geocoding fails, relies on city matching
        mock_fetch_nearby.return_value = []
        
        # Multiple Troy events to trigger variety penalties
        events = [
            {
                "title": "Troy Night Out 1",
                "category": "arts",
                "location": "Downtown Troy, NY",
                "url": "https://example.com/troy1",
            },
            {
                "title": "Troy Night Out 2",
                "category": "arts",
                "location": "Downtown Troy, NY",
                "url": "https://example.com/troy2",
            },
            {
                "title": "Troy Night Out 3",
                "category": "arts",
                "location": "Downtown Troy, NY",
                "url": "https://example.com/troy3",
            },
        ]
        
        restaurants = [
            # Troy restaurants (should be selected for Troy events)
            {
                "name": "Dinosaur Bar-B-Que",
                "cuisine": "BBQ",
                "address": "377 River St, Troy, NY",
                "url": "https://example.com/dino",
            },
            {
                "name": "Plumb Oyster Bar",
                "cuisine": "Seafood",
                "address": "7 Congress St, Troy, NY",
                "url": "https://example.com/plumb",
            },
            # Niskayuna restaurant (should NOT be selected for Troy events)
            {
                "name": "Mario's Restaurant & Pizzeria",
                "cuisine": "Italian",
                "address": "2850 River Rd, Niskayuna, NY",
                "url": "https://example.com/mario",
            },
        ]
        
        cfg = {"region": "Capital Region, NY"}
        pairings = _build_pairings(events, restaurants, cfg)
        
        assert len(pairings) == 3
        
        # All Troy events should be paired with Troy restaurants only
        # None should be paired with Niskayuna restaurant
        for pairing in pairings:
            assert "Troy" in pairing["event"]
            assert pairing["restaurant"] in ["Dinosaur Bar-B-Que", "Plumb Oyster Bar"], \
                f"Troy event '{pairing['event']}' should not be paired with '{pairing['restaurant']}' in Niskayuna"
    
    @patch('happenstance.aggregate._geocode_address')
    @patch('happenstance.aggregate._fetch_nearby_restaurants')
    def test_pairings_fallback_to_different_city_when_no_same_city_available(self, mock_fetch_nearby, mock_geocode):
        """Test that different-city restaurants are used when no same-city options exist."""
        mock_geocode.return_value = None  # Geocoding fails, relies on city matching
        mock_fetch_nearby.return_value = []
        
        events = [
            {
                "title": "Schenectady Art Walk",
                "category": "arts",
                "location": "Downtown Schenectady, NY",
                "url": "https://example.com/schenectady",
            },
        ]
        
        # Only Troy restaurants available (no Schenectady restaurants)
        restaurants = [
            {
                "name": "Dinosaur Bar-B-Que",
                "cuisine": "BBQ",
                "address": "377 River St, Troy, NY",
                "url": "https://example.com/dino",
            },
        ]
        
        cfg = {"region": "Capital Region, NY"}
        pairings = _build_pairings(events, restaurants, cfg)
        
        assert len(pairings) == 1
        # Should still create a pairing, even though city doesn't match
        assert pairings[0]["event"] == "Schenectady Art Walk"
        assert pairings[0]["restaurant"] == "Dinosaur Bar-B-Que"

