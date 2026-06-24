"""Data source integrations for fetching real restaurant and event data.

This module provides integrations with external APIs to fetch real restaurant and event data:
- Google Places API for restaurants
- Ticketmaster API for events
- Eventbrite API as an alternative event source
"""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List


def _make_request(
    url: str,
    headers: Dict[str, str] | None = None,
    method: str = "GET",
    data: Dict | None = None,
) -> Dict:
    """Make an HTTP request and return JSON response.
    
    Args:
        url: URL to request
        headers: Optional headers dict
        method: HTTP method (GET or POST)
        data: Optional data dict for POST requests
        
    Returns:
        Parsed JSON response
        
    Raises:
        ValueError: If request fails
    """
    req_data = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=req_data,
        headers=headers or {},
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        raise ValueError(f"HTTP request failed: {e}") from e


def _infer_cuisine(place_data: Dict) -> str:
    """Infer cuisine type from Google Places data."""
    types = place_data.get("types", [])
    
    # Map Google Place types to cuisine categories
    cuisine_mapping = {
        "italian_restaurant": "Italian",
        "japanese_restaurant": "Sushi",
        "chinese_restaurant": "Chinese",
        "mexican_restaurant": "Mexican",
        "french_restaurant": "French",
        "indian_restaurant": "Indian",
        "thai_restaurant": "Thai",
        "korean_restaurant": "Korean",
        "vietnamese_restaurant": "Vietnamese",
        "mediterranean_restaurant": "Mediterranean",
        "spanish_restaurant": "Spanish",
        "greek_restaurant": "Greek",
        "american_restaurant": "American",
        "bar_and_grill": "Bar & Grill",
        "barbecue_restaurant": "BBQ",
        "seafood_restaurant": "Seafood",
        "steakhouse": "Steakhouse",
        "vegetarian_restaurant": "Vegetarian",
        "vegan_restaurant": "Vegan",
        "pizza_restaurant": "Pizza",
        "bakery": "Bakery",
        "cafe": "Cafe",
    }
    
    for place_type in types:
        if place_type in cuisine_mapping:
            return cuisine_mapping[place_type]
    
    # Default fallback
    if "restaurant" in types:
        return "Restaurant"
    if "cafe" in types:
        return "Cafe"
    if "bar" in types:
        return "Bar"
    
    return "Dining"


def fetch_google_places_restaurants(
    city: str,
    region: str,
    cuisine_types: List[str] | None = None,
    count: int = 20,
) -> List[Dict]:
    """
    Fetch restaurants from Google Places API.
    
    Args:
        city: City name to search (e.g., "San Francisco", "New York")
        region: Region name for display
        cuisine_types: List of preferred cuisine types (optional)
        count: Number of restaurants to fetch
        
    Returns:
        List of restaurant dictionaries
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise ValueError("Google Places API key not provided. Set GOOGLE_PLACES_API_KEY environment variable.")
    
    # Use Text Search (New) API
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,places.types,"
            "places.rating,places.priceLevel,places.location,places.regularOpeningHours,"
            "places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri"
        ),
    }
    
    # Build search query
    cuisine_query = f" {' OR '.join(cuisine_types)}" if cuisine_types else ""
    query = f"restaurants in {city}{cuisine_query}"
    
    body = {
        "textQuery": query,
        "maxResultCount": min(count, 20),  # API limit
    }
    
    try:
        data = _make_request(
            url,
            headers=headers,
            method="POST",
            data=body
        )
    except ValueError as e:
        raise ValueError(f"Google Places API request failed: {e}") from e
    
    restaurants = []
    places = data.get("places", [])
    
    for place in places[:count]:
        name = place.get("displayName", {}).get("text", "Unknown")
        address = place.get("formattedAddress", f"{city}")
        place_id = place.get("id", "")
        place_location = place.get("location", {})
        
        # Build Google Maps URL
        url = place.get("googleMapsUri") or (
            f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://www.google.com/search?q={urllib.parse.quote(name)}+{urllib.parse.quote(city)}"
        )
        
        restaurant = {
            "id": place_id or _stable_id("restaurant", name, address),
            "name": name,
            "cuisine": _infer_cuisine(place),
            "address": address,
            "url": url,
            "match_reason": f"Popular restaurant in {city}",
        }

        if "latitude" in place_location and "longitude" in place_location:
            restaurant["location"] = {
                "lat": place_location["latitude"],
                "lng": place_location["longitude"],
            }
        if place.get("nationalPhoneNumber"):
            restaurant["phone"] = place["nationalPhoneNumber"]
        if place.get("websiteUri"):
            restaurant["website"] = place["websiteUri"]
        if place.get("regularOpeningHours", {}).get("weekdayDescriptions"):
            restaurant["hours"] = place["regularOpeningHours"]["weekdayDescriptions"]
        
        # Add rating if available
        if "rating" in place:
            restaurant["rating"] = place["rating"]
        
        # Add price level if available
        if "priceLevel" in place:
            # Google uses PRICE_LEVEL_FREE, PRICE_LEVEL_INEXPENSIVE, etc.
            price_map = {
                "PRICE_LEVEL_FREE": 0,
                "PRICE_LEVEL_INEXPENSIVE": 1,
                "PRICE_LEVEL_MODERATE": 2,
                "PRICE_LEVEL_EXPENSIVE": 3,
                "PRICE_LEVEL_VERY_EXPENSIVE": 4,
            }
            restaurant["price_level"] = price_map.get(place["priceLevel"], 2)
        
        restaurants.append(restaurant)
    
    return restaurants


def _categorize_event(event_data: Dict) -> str:
    """Infer event category from Ticketmaster classifications."""
    classifications = event_data.get("classifications", [])
    
    if not classifications:
        return "entertainment"
    
    # Get primary classification
    primary = classifications[0]
    segment = primary.get("segment", {}).get("name", "").lower()
    genre = primary.get("genre", {}).get("name", "").lower()
    
    # Map to our categories
    if "music" in segment or "music" in genre:
        return "live music"
    elif "arts" in segment or "art" in genre or "theatre" in genre:
        return "art"
    elif "sports" in segment:
        return "sports"
    elif "family" in genre or "children" in genre:
        return "family"
    else:
        return "entertainment"


def fetch_ticketmaster_events(
    city: str,
    region: str,
    categories: List[str] | None = None,
    days_ahead: int = 30,
    count: int = 20,
    state_code: str | None = None,
) -> List[Dict]:
    """
    Fetch events from Ticketmaster API.
    
    Args:
        city: City name to search
        region: Region name for display
        categories: List of preferred categories (optional)
        days_ahead: Number of days ahead to search
        count: Number of events to fetch
        
    Returns:
        List of event dictionaries
    """
    api_key = os.getenv("TICKETMASTER_API_KEY")
    if not api_key:
        raise ValueError("Ticketmaster API key not provided. Set TICKETMASTER_API_KEY environment variable.")
    
    # Calculate date range
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=days_ahead)
    
    # Build API URL
    params = {
        "apikey": api_key,
        "city": city,
        "startDateTime": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endDateTime": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "size": min(count, 200),  # API limit
        "sort": "date,asc",
    }
    state_code = state_code or os.getenv("TICKETMASTER_STATE_CODE")
    if state_code:
        params["stateCode"] = state_code
    
    # Add classification filter if categories specified
    if categories:
        # Map our categories to Ticketmaster classifications
        classification_map = {
            "live music": "music",
            "art": "arts",
            "sports": "sports",
            "family": "family",
        }
        classifications = [classification_map.get(cat, cat) for cat in categories]
        params["classificationName"] = ",".join(classifications)
    
    url = f"https://app.ticketmaster.com/discovery/v2/events.json?{urllib.parse.urlencode(params)}"
    
    try:
        data = _make_request(url)
    except Exception as e:
        raise ValueError(f"Ticketmaster API request failed: {e}") from e
    
    events = []
    embedded = data.get("_embedded", {})
    ticketmaster_events = embedded.get("events", [])
    
    for tm_event in ticketmaster_events[:count]:
        title = tm_event.get("name", "Unknown Event")
        
        # Get venue information
        venues = tm_event.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}
        venue_name = venue.get("name", city)
        city_name = venue.get("city", {}).get("name")
        state_code = venue.get("state", {}).get("stateCode")
        address_line = venue.get("address", {}).get("line1")
        location_parts = [part for part in [venue_name, city_name, state_code] if part]
        location = ", ".join(location_parts) or city
        
        # Get event date
        dates = tm_event.get("dates", {})
        start = dates.get("start", {})
        date_str = start.get("dateTime") or start.get("localDate", datetime.now(timezone.utc).isoformat())
        
        # Ensure ISO format
        try:
            event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date_iso = event_date.isoformat()
        except (ValueError, AttributeError):
            date_iso = datetime.now(timezone.utc).isoformat()
        
        # Get URL
        url = tm_event.get("url", f"https://www.ticketmaster.com/search?q={urllib.parse.quote(title)}")
        
        event = {
            "id": tm_event.get("id") or _stable_id("event", title, date_iso, location),
            "name": title,
            "title": title,
            "category": _categorize_event(tm_event),
            "date": date_iso,
            "time": start.get("localTime", ""),
            "venue": venue_name,
            "location": location,
            "url": url,
        }

        if address_line:
            event["address"] = ", ".join(part for part in [address_line, city_name, state_code] if part)
        if venue.get("location", {}).get("latitude") and venue.get("location", {}).get("longitude"):
            event["coordinates"] = {
                "lat": float(venue["location"]["latitude"]),
                "lng": float(venue["location"]["longitude"]),
            }
        
        events.append(event)
    
    return events


def fetch_eventbrite_events(
    city: str,
    region: str,
    categories: List[str] | None = None,
    days_ahead: int = 30,
    count: int = 20,
) -> List[Dict]:
    """
    Fetch events from Eventbrite API.
    
    Args:
        city: City name to search
        region: Region name for display
        categories: List of preferred categories (optional)
        days_ahead: Number of days ahead to search
        count: Number of events to fetch
        
    Returns:
        List of event dictionaries
    """
    api_key = os.getenv("EVENTBRITE_API_KEY")
    if not api_key:
        raise ValueError("Eventbrite API key not provided. Set EVENTBRITE_API_KEY environment variable.")
    
    # Calculate date range
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=days_ahead)
    
    # Build API URL
    params = {
        "location.address": city,
        "start_date.range_start": start_date.isoformat(),
        "start_date.range_end": end_date.isoformat(),
        "expand": "venue",
    }
    
    url = f"https://www.eventbriteapi.com/v3/events/search/?{urllib.parse.urlencode(params)}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    
    try:
        data = _make_request(url, headers)
    except Exception as e:
        raise ValueError(f"Eventbrite API request failed: {e}") from e
    
    events = []
    eventbrite_events = data.get("events", [])
    
    for eb_event in eventbrite_events[:count]:
        title = eb_event.get("name", {}).get("text", "Unknown Event")
        
        # Get venue
        venue = eb_event.get("venue", {})
        location = venue.get("name", city) if venue else city
        
        # Get date
        start = eb_event.get("start", {})
        date_str = start.get("utc", datetime.now(timezone.utc).isoformat())
        
        # Get URL
        url = eb_event.get("url", f"https://www.eventbrite.com/d/{city.replace(' ', '-').lower()}/events/")
        
        # Infer category (Eventbrite doesn't have strong categorization in basic response)
        category = "entertainment"
        description = eb_event.get("description", {}).get("text", "").lower()
        if any(word in description or word in title.lower() for word in ["music", "concert", "band"]):
            category = "live music"
        elif any(word in description or word in title.lower() for word in ["art", "gallery", "museum"]):
            category = "art"
        elif any(word in description or word in title.lower() for word in ["sport", "game", "race"]):
            category = "sports"
        elif any(word in description or word in title.lower() for word in ["family", "kids", "children"]):
            category = "family"
        
        event = {
            "id": eb_event.get("id") or _stable_id("event", title, date_str, location),
            "name": title,
            "title": title,
            "category": category,
            "date": date_str,
            "venue": location,
            "location": location,
            "url": url,
        }
        
        events.append(event)
    
    return events


# Keep AI functions for backward compatibility
def _parse_json_from_text(text: str) -> Any:
    """
    Extract JSON from AI response text.
    
    Args:
        text: Text potentially containing JSON
        
    Returns:
        Parsed JSON object or None
    """
    # Try to find JSON in markdown code blocks first
    json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\]|\{[\s\S]*?\})\s*```', text, re.MULTILINE)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find raw JSON array
    json_match = re.search(r'(\[[\s\S]*?\])', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find raw JSON object
    json_match = re.search(r'(\{[\s\S]*?\})', text)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    return None


def _load_real_data_from_script(data_type: str) -> List[Dict]:
    """Load real data from the generate_real_data.py script."""
    import importlib.util
    from pathlib import Path
    
    # Get the path to the script
    script_path = Path(__file__).parent.parent / "scripts" / "generate_real_data.py"
    
    # Load the module dynamically without adding to sys.modules
    spec = importlib.util.spec_from_file_location("_generate_real_data_temp", script_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load data script from {script_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get the data
    if data_type == "restaurants":
        return module.RESTAURANTS_DATA
    elif data_type == "events":
        return module.EVENTS_DATA
    else:
        raise ValueError(f"Unknown data type: {data_type}")


def fetch_ai_restaurants(
    region: str,
    city: str | None = None,
    cuisine_types: List[str] | None = None,
    count: int = 20,
    ai_response: str | None = None,
) -> List[Dict]:
    """
    Fetch restaurants using AI-powered search results.
    
    Args:
        region: Region name for display purposes
        city: City name for search
        cuisine_types: List of preferred cuisine types
        count: Number of restaurants to fetch
        ai_response: Pre-fetched AI response (from web_search tool)
        
    Returns:
        List of restaurant dictionaries
    """
    city_name = city or region
    
    if not ai_response:
        # Check if response was provided via environment variable
        ai_response = os.getenv("AI_RESTAURANTS_DATA")
    
    if not ai_response:
        # Try to load from the real data script
        try:
            data = _load_real_data_from_script("restaurants")
            return data[:count]
        except Exception as e:
            raise ValueError(
                f"No AI response provided for restaurants and failed to load real data: {e}. "
                "Either pass ai_response parameter or set AI_RESTAURANTS_DATA environment variable."
            ) from e
    
    try:
        # Try to parse JSON from response
        data = _parse_json_from_text(ai_response)
        
        if data and isinstance(data, list):
            # Validate and clean the data
            restaurants = []
            for item in data[:count]:
                if isinstance(item, dict) and "name" in item:
                    restaurant = {
                        "name": item.get("name", "Unknown"),
                        "cuisine": item.get("cuisine", "Restaurant"),
                        "address": item.get("address", f"{city_name} area"),
                        "url": item.get("url", f"https://www.google.com/search?q={item.get('name', 'restaurant').replace(' ', '+')}+{city_name.replace(' ', '+')}"),
                        "match_reason": item.get("match_reason", f"Popular restaurant in {city_name}"),
                    }
                    # Optional fields
                    if "rating" in item:
                        restaurant["rating"] = item["rating"]
                    if "price_level" in item:
                        restaurant["price_level"] = item["price_level"]
                    restaurants.append(restaurant)
            
            if restaurants:
                return restaurants
        
        # If parsing failed, raise error to trigger fallback
        raise ValueError("Failed to parse restaurant data from AI response")
        
    except Exception as e:
        raise ValueError(f"Failed to fetch restaurants using AI: {e}") from e


def fetch_ai_events(
    region: str,
    city: str | None = None,
    categories: List[str] | None = None,
    days_ahead: int = 30,
    count: int = 20,
    ai_response: str | None = None,
) -> List[Dict]:
    """
    Fetch events using AI-powered search results.
    
    Args:
        region: Region name for display purposes
        city: City name for search  
        categories: List of preferred event categories
        days_ahead: Number of days ahead to search for events
        count: Number of events to fetch
        ai_response: Pre-fetched AI response (from web_search tool)
        
    Returns:
        List of event dictionaries
    """
    city_name = city or region
    
    if not ai_response:
        # Check if response was provided via environment variable
        ai_response = os.getenv("AI_EVENTS_DATA")
    
    if not ai_response:
        # Try to load from the real data script
        try:
            data = _load_real_data_from_script("events")
            return data[:count]
        except Exception as e:
            raise ValueError(
                f"No AI response provided for events and failed to load real data: {e}. "
                "Either pass ai_response parameter or set AI_EVENTS_DATA environment variable."
            ) from e
    
    try:
        # Try to parse JSON from response
        data = _parse_json_from_text(ai_response)
        
        if data and isinstance(data, list):
            # Validate and clean the data
            events = []
            for item in data[:count]:
                if isinstance(item, dict) and "title" in item:
                    event = {
                        "id": item.get("id") or _stable_id("event", item.get("title", "Unknown Event"), item.get("date", ""), item.get("location", "")),
                        "name": item.get("name") or item.get("title", "Unknown Event"),
                        "title": item.get("title", "Unknown Event"),
                        "category": item.get("category", "entertainment"),
                        "date": item.get("date", datetime.now(timezone.utc).isoformat()),
                        "time": item.get("time", ""),
                        "venue": item.get("venue") or item.get("location", f"{city_name}"),
                        "location": item.get("location", f"{city_name}"),
                        "url": item.get("url", f"https://www.google.com/search?q={item.get('title', 'event').replace(' ', '+')}+{city_name.replace(' ', '+')}"),
                    }
                    if "coordinates" in item:
                        event["coordinates"] = item["coordinates"]
                    if "location" in item and isinstance(item["location"], dict):
                        event["coordinates"] = item["location"]
                    events.append(event)
            
            if events:
                return events
        
        # If parsing failed, raise error to trigger fallback
        raise ValueError("Failed to parse event data from AI response")
        
    except Exception as e:
        raise ValueError(f"Failed to fetch events using AI: {e}") from e


def _stable_id(*parts: str) -> str:
    value = "-".join(str(part) for part in parts if part)
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:96] or "item"


def _roll_static_events_forward(events: List[Dict], days_ahead: int = 30) -> List[Dict]:
    """Move baked fallback events into the current window while preserving order and times."""
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    if not events:
        return []

    parsed: List[tuple[Dict, datetime]] = []
    for item in events:
        try:
            dt = datetime.fromisoformat(str(item.get("date", "")).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            dt = now
        parsed.append((item, dt))

    cutoff = now + timedelta(days=days_ahead)
    if any(now <= dt <= cutoff for _, dt in parsed):
        return [dict(item) for item, _ in parsed]

    rolled = []
    span = max(1, min(days_ahead, len(parsed) + 2))
    for index, (item, old_dt) in enumerate(parsed):
        new_dt = now + timedelta(days=index % span)
        new_dt = new_dt.replace(hour=old_dt.hour, minute=old_dt.minute, second=0, microsecond=0)
        if new_dt < now:
            new_dt += timedelta(days=1)
        copy = dict(item)
        copy["date"] = new_dt.isoformat()
        if old_dt.hour or old_dt.minute:
            copy["time"] = f"{old_dt.hour:02d}:{old_dt.minute:02d}"
        copy.setdefault("match_reason", "Rolled forward from local demo seed data")
        rolled.append(copy)
    return rolled
