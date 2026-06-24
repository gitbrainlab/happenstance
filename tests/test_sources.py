"""Tests for data source integrations."""
import os
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from happenstance.sources import (
    _categorize_event,
    _infer_cuisine,
    _parse_json_from_text,
    fetch_barpeople_events,
    fetch_eventbrite_events,
    fetch_google_places_restaurants,
    fetch_ticketmaster_events,
)


class TestParseJsonFromText:
    """Tests for JSON parsing from AI responses."""
    
    def test_parse_json_from_markdown_block(self):
        text = """Here's the data:
```json
[{"name": "Test Restaurant", "cuisine": "Italian"}]
```
"""
        result = _parse_json_from_text(text)
        assert result == [{"name": "Test Restaurant", "cuisine": "Italian"}]
    
    def test_parse_json_array(self):
        text = '[{"name": "Test", "cuisine": "Italian"}]'
        result = _parse_json_from_text(text)
        assert result == [{"name": "Test", "cuisine": "Italian"}]
    
    def test_parse_json_object(self):
        text = '{"name": "Test", "cuisine": "Italian"}'
        result = _parse_json_from_text(text)
        assert result == {"name": "Test", "cuisine": "Italian"}
    
    def test_parse_invalid_json(self):
        text = "This is not JSON"
        result = _parse_json_from_text(text)
        assert result is None


class TestInferCuisine:
    """Tests for cuisine inference from Google Places types."""
    
    def test_infer_italian(self):
        place_data = {"types": ["italian_restaurant", "restaurant"]}
        assert _infer_cuisine(place_data) == "Italian"
    
    def test_infer_sushi(self):
        place_data = {"types": ["japanese_restaurant", "restaurant"]}
        assert _infer_cuisine(place_data) == "Sushi"
    
    def test_infer_generic_restaurant(self):
        place_data = {"types": ["restaurant", "food"]}
        assert _infer_cuisine(place_data) == "Restaurant"
    
    def test_infer_cafe(self):
        place_data = {"types": ["cafe"]}
        assert _infer_cuisine(place_data) == "Cafe"
    
    def test_infer_default(self):
        place_data = {"types": ["point_of_interest"]}
        assert _infer_cuisine(place_data) == "Dining"


class TestCategorizeEvent:
    """Tests for event categorization from Ticketmaster data."""
    
    def test_categorize_music(self):
        event_data = {
            "classifications": [
                {"segment": {"name": "Music"}, "genre": {"name": "Rock"}}
            ]
        }
        assert _categorize_event(event_data) == "live music"
    
    def test_categorize_arts(self):
        event_data = {
            "classifications": [
                {"segment": {"name": "Arts & Theatre"}, "genre": {"name": "Theatre"}}
            ]
        }
        assert _categorize_event(event_data) == "art"
    
    def test_categorize_sports(self):
        event_data = {
            "classifications": [
                {"segment": {"name": "Sports"}, "genre": {"name": "Football"}}
            ]
        }
        assert _categorize_event(event_data) == "sports"
    
    def test_categorize_family(self):
        event_data = {
            "classifications": [
                {"segment": {"name": "Miscellaneous"}, "genre": {"name": "Family"}}
            ]
        }
        assert _categorize_event(event_data) == "family"
    
    def test_categorize_default(self):
        event_data = {"classifications": []}
        assert _categorize_event(event_data) == "entertainment"


class TestGooglePlacesRestaurants:
    """Tests for Google Places API integration."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="Google Places API key not provided"):
            fetch_google_places_restaurants("San Francisco", "Sample City")
    
    @patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test_key"})
    @patch("happenstance.sources._make_request")
    def test_successful_fetch(self, mock_request):
        """Test successful restaurant fetch."""
        mock_request.return_value = {
            "places": [
                {
                    "displayName": {"text": "Test Restaurant"},
                    "formattedAddress": "123 Main St, San Francisco",
                    "id": "place123",
                    "types": ["italian_restaurant"],
                    "rating": 4.5,
                    "priceLevel": "PRICE_LEVEL_MODERATE",
                    "websiteUri": "https://example.com",
                }
            ]
        }
        
        restaurants = fetch_google_places_restaurants("San Francisco", "Sample City")
        
        assert len(restaurants) == 1
        assert restaurants[0]["name"] == "Test Restaurant"
        assert restaurants[0]["cuisine"] == "Italian"
        assert restaurants[0]["rating"] == 4.5
        assert restaurants[0]["price_level"] == 2
        assert "menu_url" in restaurants[0]
        assert restaurants[0]["menu_status"] == "search"

    @patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": "test_key"})
    @patch("happenstance.sources._make_request")
    def test_fetch_balances_target_areas(self, mock_request):
        """Test that regional searches sample each requested target area."""
        def response_for_area(*_, **kwargs):
            area = kwargs["data"]["textQuery"].replace("restaurants in ", "")
            return {
                "places": [
                    {
                        "displayName": {"text": f"{area} Bistro"},
                        "formattedAddress": f"1 Main St, {area}, NY",
                        "id": f"place-{area.lower().replace(' ', '-')}",
                        "types": ["restaurant"],
                        "rating": 4.5,
                        "userRatingCount": 100,
                    }
                ]
            }

        mock_request.side_effect = response_for_area

        restaurants = fetch_google_places_restaurants(
            "Capital Region, NY",
            "Capital Region, NY",
            count=3,
            areas=["Albany", "Troy", "Lake George"],
        )

        assert [restaurant["name"] for restaurant in restaurants] == [
            "Albany Bistro",
            "Troy Bistro",
            "Lake George Bistro",
        ]
        assert mock_request.call_count == 4


class TestTicketmasterEvents:
    """Tests for Ticketmaster API integration."""
    
    def test_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="Ticketmaster API key not provided"):
            fetch_ticketmaster_events("San Francisco", "Sample City")
    
    @patch.dict(os.environ, {"TICKETMASTER_API_KEY": "test_key"})
    @patch("happenstance.sources._make_request")
    def test_successful_fetch(self, mock_request):
        """Test successful event fetch."""
        mock_request.return_value = {
            "_embedded": {
                "events": [
                    {
                        "name": "Test Concert",
                        "classifications": [
                            {"segment": {"name": "Music"}, "genre": {"name": "Rock"}}
                        ],
                        "dates": {
                            "start": {
                                "dateTime": "2025-12-20T19:00:00Z"
                            }
                        },
                        "_embedded": {
                            "venues": [
                                {"name": "Test Venue"}
                            ]
                        },
                        "url": "https://www.ticketmaster.com/event/123",
                        "priceRanges": [
                            {"type": "standard", "currency": "USD", "min": 25.0, "max": 75.0}
                        ],
                    }
                ]
            }
        }
        
        events = fetch_ticketmaster_events("San Francisco", "Sample City")
        
        assert len(events) == 1
        assert events[0]["title"] == "Test Concert"
        assert events[0]["category"] == "live music"
        assert events[0]["location"] == "Test Venue"
        assert events[0]["ticket_url"] == "https://www.ticketmaster.com/event/123"
        assert events[0]["price_note"] == "$25-$75"


class TestEventbriteEvents:
    """Tests for Eventbrite API integration."""
    
    def test_missing_api_key(self):
        """Test that missing API key raises ValueError."""
        with pytest.raises(ValueError, match="Eventbrite API key not provided"):
            fetch_eventbrite_events("San Francisco", "Sample City")
    
    @patch.dict(os.environ, {"EVENTBRITE_API_KEY": "test_token"})
    @patch("happenstance.sources._make_request")
    def test_successful_fetch(self, mock_request):
        """Test successful event fetch."""
        mock_request.return_value = {
            "events": [
                {
                    "name": {"text": "Test Event"},
                    "description": {"text": "A music concert in the park"},
                    "start": {"utc": "2025-12-20T19:00:00Z"},
                    "venue": {"name": "Test Venue"},
                    "url": "https://www.eventbrite.com/e/123"
                }
            ]
        }
        
        events = fetch_eventbrite_events("San Francisco", "Sample City")
        
        assert len(events) == 1
        assert events[0]["title"] == "Test Event"
        assert events[0]["category"] == "live music"  # Inferred from description
        assert events[0]["location"] == "Test Venue"


class TestBarPeopleEvents:
    """Tests for BarPeople text listing parsing."""

    def test_fetch_barpeople_dated_live_music(self):
        html = """
        <h2>Saratoga Springs Live Music</h2>
        <p>6/24 5:30 PM Next Chapter- Wishing Well</p>
        <p>6/26 7:00 PM Late Night Philosophers & DJ Tune- Night Owl</p>
        """
        events = fetch_barpeople_events(
            "Capital Region, NY",
            pages=[{"kind": "live_music", "area": "Saratoga Springs", "url": "https://www.barpeople.com/test", "html": html}],
            now=datetime(2026, 6, 24, 12, tzinfo=timezone.utc),
        )

        assert [event["title"] for event in events] == [
            "Next Chapter at Wishing Well",
            "Late Night Philosophers & DJ Tune at Night Owl",
        ]
        assert events[0]["category"] == "live music"
        assert events[0]["source"] == "BarPeople"
        assert events[0]["ticket_status"] == "check venue"
        assert events[0]["price_note"] == "Check venue"
        assert events[0]["location"] == "Wishing Well, Saratoga Springs, NY"

    def test_fetch_barpeople_weekly_bar_events(self):
        html = """
        <h2>Bar Events</h2>
        <h3>Karaoke</h3>
        <p>Wednesday:</p>
        <p>8:00 PM Saratoga Wine Bar- (Saratoga Springs)</p>
        <h3>Trivia</h3>
        <p>Thursday:</p>
        <p>Parting Glass - 6:00 PM (Saratoga Springs)</p>
        """
        events = fetch_barpeople_events(
            "Capital Region, NY",
            pages=[{"kind": "bar_events", "area": "Capital Region", "url": "https://www.barpeople.com/bar", "html": html}],
            now=datetime(2026, 6, 24, 12, tzinfo=timezone.utc),
        )

        assert [event["title"] for event in events] == [
            "Karaoke at Saratoga Wine Bar",
            "Trivia at Parting Glass",
        ]
        assert [event["category"] for event in events] == ["karaoke", "trivia"]
        assert events[0]["date"].startswith("2026-06-24T20:00:00")
        assert events[1]["date"].startswith("2026-06-25T18:00:00")

    def test_fetch_barpeople_dj_events(self):
        html = """
        <h3>DJ Events</h3>
        <h3>Sound Bar</h3>
        <h4>Saratoga Springs</h4>
        <p>Friday & Saturday Nights</p>
        """
        events = fetch_barpeople_events(
            "Capital Region, NY",
            pages=[{"kind": "dj", "area": "Saratoga Springs", "url": "https://www.barpeople.com/dj", "html": html}],
            now=datetime(2026, 6, 24, 12, tzinfo=timezone.utc),
        )

        assert [event["title"] for event in events] == ["DJ night at Sound Bar", "DJ night at Sound Bar"]
        assert [event["category"] for event in events] == ["dj", "dj"]
        assert events[0]["date"].startswith("2026-06-26T21:00:00")
        assert events[1]["date"].startswith("2026-06-27T21:00:00")
