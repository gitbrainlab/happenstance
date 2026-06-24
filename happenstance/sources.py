"""Data source integrations for fetching real restaurant and event data.

This module provides integrations with external APIs to fetch real restaurant and event data:
- Google Places API for restaurants
- Ticketmaster API for events
- Eventbrite API as an alternative event source
"""

from __future__ import annotations

import json
import math
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from datetime import time as datetime_time
from html.parser import HTMLParser
from typing import Any, Dict, List
from zoneinfo import ZoneInfo


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


def _make_text_request(url: str, headers: Dict[str, str] | None = None) -> str:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise ValueError(f"HTTP text request failed: {e}") from e


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
    areas: List[str] | None = None,
) -> List[Dict]:
    """
    Fetch restaurants from Google Places API.
    
    Args:
        city: City name to search (e.g., "San Francisco", "New York")
        region: Region name for display
        cuisine_types: List of preferred cuisine types (optional)
        count: Number of restaurants to fetch
        areas: Area labels to search for broader regional coverage
        
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
            "places.primaryType,places.primaryTypeDisplayName,places.rating,places.userRatingCount,"
            "places.priceLevel,places.location,places.regularOpeningHours,places.currentOpeningHours,"
            "places.businessStatus,places.nationalPhoneNumber,places.websiteUri,places.googleMapsUri,"
            "places.editorialSummary"
        ),
    }

    restaurants = []
    seen: set[str] = set()
    search_areas = _dedupe_strings([*(areas or []), city])
    per_search_count = min(10, max(3, math.ceil(count / max(1, len(search_areas))) + 2))
    buckets: list[list[Dict]] = []

    for area in search_areas:
        body = {
            "textQuery": f"restaurants in {area}",
            "maxResultCount": min(per_search_count, 20),
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

        bucket: list[Dict] = []
        for place in data.get("places", []):
            restaurant = _restaurant_from_google_place(place, area)
            key = restaurant.get("google_place_id") or _stable_id(restaurant["name"], restaurant["address"])
            if key in seen:
                continue
            seen.add(key)
            bucket.append(restaurant)
        bucket.sort(key=_restaurant_quality_score, reverse=True)
        buckets.append(bucket)

    restaurants.extend(_balanced_restaurant_selection(buckets, count))
    if len(restaurants) < count and cuisine_types:
        for cuisine in cuisine_types:
            if len(restaurants) >= count:
                break
            body = {
                "textQuery": f"{cuisine} restaurants in {city}",
                "maxResultCount": min(5, count - len(restaurants), 20),
            }
            try:
                data = _make_request(url, headers=headers, method="POST", data=body)
            except ValueError as e:
                raise ValueError(f"Google Places API request failed: {e}") from e
            for place in data.get("places", []):
                restaurant = _restaurant_from_google_place(place, city)
                key = restaurant.get("google_place_id") or _stable_id(restaurant["name"], restaurant["address"])
                if key in seen:
                    continue
                seen.add(key)
                restaurants.append(restaurant)
                if len(restaurants) >= count:
                    break

    return restaurants[:count]


def _balanced_restaurant_selection(buckets: List[List[Dict]], count: int) -> List[Dict]:
    selected: list[Dict] = []
    max_bucket_size = max((len(bucket) for bucket in buckets), default=0)
    for index in range(max_bucket_size):
        for bucket in buckets:
            if index >= len(bucket):
                continue
            selected.append(bucket[index])
            if len(selected) >= count:
                return selected
    return selected


def _restaurant_quality_score(restaurant: Dict) -> float:
    try:
        rating = float(restaurant.get("rating") or 0)
    except (TypeError, ValueError):
        rating = 0.0
    try:
        review_count = int(restaurant.get("review_count") or 0)
    except (TypeError, ValueError):
        review_count = 0
    return rating * 10 + min(math.log10(review_count + 1) * 4, 12)


def _restaurant_from_google_place(place: Dict, area: str) -> Dict:
    name = place.get("displayName", {}).get("text", "Unknown")
    address = place.get("formattedAddress", f"{area}")
    place_id = place.get("id", "")
    place_location = place.get("location", {})

    # Build Google Maps URL
    url = place.get("googleMapsUri") or (
        f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://www.google.com/search?q={urllib.parse.quote(name)}+{urllib.parse.quote(area)}"
    )
    summary = place.get("editorialSummary", {}).get("text")
    type_labels = _place_type_labels(place)

    restaurant = {
        "id": place_id or _stable_id("restaurant", name, address),
        "google_place_id": place_id,
        "name": name,
        "cuisine": _infer_cuisine(place),
        "address": address,
        "url": url,
        "menu_url": _menu_search_url(name, address),
        "menu_status": "search",
        "match_reason": summary or f"Popular restaurant in {area}",
        "tags": type_labels,
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
    if place.get("regularOpeningHours", {}).get("openNow") is not None:
        restaurant["open_now"] = place["regularOpeningHours"]["openNow"]
    if place.get("currentOpeningHours", {}).get("weekdayDescriptions"):
        restaurant["current_hours"] = place["currentOpeningHours"]["weekdayDescriptions"]
    if place.get("businessStatus"):
        restaurant["business_status"] = place["businessStatus"]

    # Add rating if available
    if "rating" in place:
        restaurant["rating"] = place["rating"]
    if "userRatingCount" in place:
        restaurant["review_count"] = place["userRatingCount"]

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

    return restaurant


def _menu_search_url(name: str, address: str) -> str:
    query = f"{name} menu {address}".strip()
    return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"


def _place_type_labels(place: Dict) -> List[str]:
    labels: list[str] = []
    display = place.get("primaryTypeDisplayName", {}).get("text")
    if display:
        labels.append(display)
    for place_type in place.get("types", []):
        label = str(place_type).replace("_", " ").title()
        if label and label not in labels:
            labels.append(label)
    return labels[:8]


def _dedupe_strings(values: List[str]) -> List[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


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
            "ticket_url": url,
            "ticket_status": dates.get("status", {}).get("code") or "ticketed",
        }

        price = _ticketmaster_price_summary(tm_event)
        if price:
            event.update(price)

        if address_line:
            event["address"] = ", ".join(part for part in [address_line, city_name, state_code] if part)
        if venue.get("location", {}).get("latitude") and venue.get("location", {}).get("longitude"):
            event["coordinates"] = {
                "lat": float(venue["location"]["latitude"]),
                "lng": float(venue["location"]["longitude"]),
            }
        
        events.append(event)
    
    return events


def _ticketmaster_price_summary(tm_event: Dict) -> Dict:
    ranges = tm_event.get("priceRanges") or []
    if not ranges:
        return {}
    first = ranges[0]
    currency = first.get("currency", "USD")
    minimum = first.get("min")
    maximum = first.get("max")
    payload: Dict[str, Any] = {"price_currency": currency}
    if minimum is not None:
        payload["price_min"] = minimum
    if maximum is not None:
        payload["price_max"] = maximum
    if minimum is not None and maximum is not None:
        if minimum == maximum:
            payload["price_note"] = f"{_format_price(minimum, currency)}"
        else:
            payload["price_note"] = f"{_format_price(minimum, currency)}-{_format_price(maximum, currency)}"
    elif minimum is not None:
        payload["price_note"] = f"from {_format_price(minimum, currency)}"
    elif maximum is not None:
        payload["price_note"] = f"up to {_format_price(maximum, currency)}"
    return payload


def _format_price(value: Any, currency: str) -> str:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    symbol = "$" if currency == "USD" else f"{currency} "
    if amount.is_integer():
        return f"{symbol}{int(amount)}"
    return f"{symbol}{amount:.2f}"


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
            "ticket_url": url,
            "ticket_status": "ticketed",
        }
        
        events.append(event)
    
    return events


BARPEOPLE_SOURCE_NOTE = "BarPeople weekly listing; call the venue to confirm."
BARPEOPLE_TZ = ZoneInfo("America/New_York")

BARPEOPLE_PAGES = [
    {"kind": "live_music", "area": "Saratoga Springs", "url": "https://www.barpeople.com/saratoga-springs-weekly-live-music"},
    {"kind": "live_music", "area": "Albany", "url": "https://www.barpeople.com/albany-county-weekly-live-music"},
    {"kind": "live_music", "area": "Fulton County", "url": "https://www.barpeople.com/fulton-county-weekly-live-music"},
    {"kind": "live_music", "area": "Rensselaer County", "url": "https://www.barpeople.com/rensselaer-county-weekly-live-music"},
    {"kind": "live_music", "area": "Saratoga County", "url": "https://www.barpeople.com/saratoga-county-weekly-live-music"},
    {"kind": "live_music", "area": "Schenectady County", "url": "https://www.barpeople.com/schenectady-county-weekly-live-music"},
    {"kind": "live_music", "area": "Warren County", "url": "https://www.barpeople.com/warren-county-weekly-live-music"},
    {"kind": "live_music", "area": "Washington County", "url": "https://www.barpeople.com/washington-county-weekly-live-music"},
    {"kind": "dj", "area": "Saratoga Springs", "url": "https://www.barpeople.com/dj-events"},
    {"kind": "bar_events", "area": "Capital Region", "url": "https://www.barpeople.com/bar-events-1"},
]

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

TIME_RE = re.compile(r"(?P<time>\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?))", re.IGNORECASE)
DATED_BARPEOPLE_RE = re.compile(
    r"(?P<month>\d{1,2})/(?P<day>\d{1,2})\s*(?P<time>\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?))\s*(?P<detail>.+)",
    re.IGNORECASE,
)


class _VisibleTextParser(HTMLParser):
    block_tags = {"br", "p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def lines(self) -> list[str]:
        text = "".join(self.parts).replace("\xa0", " ").replace("\u200d", " ")
        return [_clean_barpeople_line(line) for line in text.splitlines() if _clean_barpeople_line(line)]


def fetch_barpeople_events(
    region: str,
    days_ahead: int = 45,
    count: int = 120,
    pages: List[Dict] | None = None,
    now: datetime | None = None,
) -> List[Dict]:
    """Fetch live music, DJ, and bar-event listings from BarPeople pages."""
    now = (now or datetime.now(timezone.utc)).astimezone(BARPEOPLE_TZ)
    page_specs = pages or BARPEOPLE_PAGES
    events: list[Dict] = []
    headers = {"User-Agent": "Happenstance/1.0 (+https://capitaldistrict.io)"}

    for page in page_specs:
        url = str(page.get("url") or "")
        if not url:
            continue
        html = str(page.get("html") or "")
        if not html:
            try:
                html = _make_text_request(url, headers=headers)
            except ValueError as e:
                print(f"Warning: Failed to fetch BarPeople page {url}: {e}")
                continue
        lines = _html_to_text_lines(html)
        kind = str(page.get("kind") or "live_music")
        if kind == "dj":
            events.extend(_parse_barpeople_dj_page(lines, page, now, days_ahead))
        else:
            events.extend(_parse_barpeople_listing_page(lines, page, now, days_ahead))

    events = _dedupe_events(events)
    events.sort(key=lambda event: event["date"])
    return events[:count]


def _html_to_text_lines(html: str) -> list[str]:
    parser = _VisibleTextParser()
    parser.feed(html)
    parser.close()
    return parser.lines()


def _parse_barpeople_listing_page(lines: list[str], page: Dict, now: datetime, days_ahead: int) -> list[Dict]:
    events: list[Dict] = []
    page_url = str(page.get("url") or "https://www.barpeople.com/")
    page_kind = str(page.get("kind") or "live_music")
    current_area = str(page.get("area") or "Capital Region")
    current_activity = "live music" if page_kind == "live_music" else "bar event"
    current_weekday: int | None = None

    for line in lines:
        activity = _barpeople_activity_heading(line)
        if activity:
            current_activity = activity
            current_weekday = None
            continue

        weekday = _barpeople_weekday(line)
        if weekday is not None:
            current_weekday = weekday
            continue

        area = _barpeople_area_heading(line)
        if area:
            current_area = area
            continue

        dated = _parse_barpeople_dated_line(line, current_area, current_activity, page_url, now, days_ahead)
        if dated:
            events.append(dated)
            continue

        if current_weekday is not None:
            weekly = _parse_barpeople_weekly_line(
                line,
                current_area,
                current_activity,
                current_weekday,
                page_url,
                now,
                days_ahead,
            )
            if weekly:
                events.append(weekly)

    return events


def _parse_barpeople_dj_page(lines: list[str], page: Dict, now: datetime, days_ahead: int) -> list[Dict]:
    events: list[Dict] = []
    page_url = str(page.get("url") or "https://www.barpeople.com/dj-events")
    venue = ""
    area = str(page.get("area") or "Saratoga Springs")

    for line in lines:
        lower = line.lower()
        if lower in {"dj events", "events", "contact us", "stay in the loop"}:
            continue
        if "friday" in lower and "saturday" in lower and "night" in lower and venue:
            for weekday in (WEEKDAYS["friday"], WEEKDAYS["saturday"]):
                event_dt = _next_weekday_datetime(now, weekday, datetime_time(21, 0))
                if _in_barpeople_window(event_dt, now, days_ahead):
                    events.append(
                        _barpeople_event(
                            title=f"DJ night at {venue}",
                            category="dj",
                            event_dt=event_dt,
                            time_label="9:00 PM",
                            venue=venue,
                            area=area,
                            url=page_url,
                            description=f"Recurring DJ night listed by BarPeople. {BARPEOPLE_SOURCE_NOTE}",
                            tags=["barpeople", "dj", "nightlife"],
                        )
                    )
            continue
        if _looks_like_barpeople_area(line):
            area = _title_area(line)
            continue
        if _looks_like_barpeople_venue(line):
            venue = _title_area(line)

    return events


def _parse_barpeople_dated_line(
    line: str,
    current_area: str,
    activity: str,
    page_url: str,
    now: datetime,
    days_ahead: int,
) -> Dict | None:
    match = DATED_BARPEOPLE_RE.search(line)
    if not match:
        return None
    event_time = _parse_barpeople_time(match.group("time"))
    if not event_time:
        return None
    event_dt = _barpeople_date_for(int(match.group("month")), int(match.group("day")), event_time, now)
    if not _in_barpeople_window(event_dt, now, days_ahead):
        return None
    detail = _clean_barpeople_line(match.group("detail"))
    performer, venue = _split_barpeople_live_detail(detail)
    if not venue:
        return None
    category = _barpeople_category(activity, detail)
    return _barpeople_event(
        title=_barpeople_title(category, performer, venue),
        category=category,
        event_dt=event_dt,
        time_label=_format_barpeople_time(event_time),
        venue=venue,
        area=current_area,
        url=page_url,
        description=f"{detail}. {BARPEOPLE_SOURCE_NOTE}",
        tags=["barpeople", category, "local"],
    )


def _parse_barpeople_weekly_line(
    line: str,
    current_area: str,
    activity: str,
    weekday: int,
    page_url: str,
    now: datetime,
    days_ahead: int,
) -> Dict | None:
    match = TIME_RE.search(line)
    if not match:
        return None
    event_time = _parse_barpeople_time(match.group("time"))
    if not event_time:
        return None
    event_dt = _next_weekday_datetime(now, weekday, event_time)
    if not _in_barpeople_window(event_dt, now, days_ahead):
        return None

    before = _clean_barpeople_line(line[: match.start()].strip(" -"))
    after = _clean_barpeople_line(line[match.end() :].strip(" -"))
    area = _parenthetical_area(line) or current_area
    detail = _strip_parenthetical_area(_clean_barpeople_line(" ".join(part for part in [before, after] if part)))
    if not detail:
        return None

    if activity == "live music":
        performer, venue = _split_barpeople_live_detail(detail)
        category = _barpeople_category(activity, detail)
        title = _barpeople_title(category, performer, venue)
    else:
        venue, descriptor = _split_barpeople_bar_detail(detail)
        category = _barpeople_category(activity, detail)
        title = _barpeople_title(category, descriptor, venue)

    if not venue:
        return None
    return _barpeople_event(
        title=title,
        category=category,
        event_dt=event_dt,
        time_label=_format_barpeople_time(event_time),
        venue=venue,
        area=area,
        url=page_url,
        description=f"Recurring {category} listing from BarPeople. {BARPEOPLE_SOURCE_NOTE}",
        tags=["barpeople", category, "recurring"],
    )


def _barpeople_event(
    title: str,
    category: str,
    event_dt: datetime,
    time_label: str,
    venue: str,
    area: str,
    url: str,
    description: str,
    tags: list[str],
) -> Dict:
    venue = _clean_barpeople_line(venue)
    area = _title_area(area or "Capital Region")
    location = ", ".join(part for part in [venue, area, "NY"] if part)
    return {
        "id": _stable_id("barpeople", title, event_dt.date().isoformat(), venue, area),
        "name": title,
        "title": title,
        "category": category,
        "date": event_dt.isoformat(),
        "time": time_label,
        "venue": venue,
        "location": location,
        "url": url,
        "source": "BarPeople",
        "source_url": url,
        "source_note": BARPEOPLE_SOURCE_NOTE,
        "description": description,
        "tags": _dedupe_strings(tags),
        "ticket_status": "check venue",
        "price_note": "Check venue",
    }


def _barpeople_date_for(month: int, day: int, event_time: datetime_time, now: datetime) -> datetime:
    event_dt = datetime(now.year, month, day, event_time.hour, event_time.minute, tzinfo=BARPEOPLE_TZ)
    if event_dt < now - timedelta(days=30):
        event_dt = event_dt.replace(year=now.year + 1)
    return event_dt


def _next_weekday_datetime(now: datetime, weekday: int, event_time: datetime_time) -> datetime:
    days_until = (weekday - now.weekday()) % 7
    candidate = datetime.combine((now + timedelta(days=days_until)).date(), event_time, tzinfo=BARPEOPLE_TZ)
    if candidate < now:
        candidate += timedelta(days=7)
    return candidate


def _in_barpeople_window(event_dt: datetime, now: datetime, days_ahead: int) -> bool:
    return now <= event_dt <= now + timedelta(days=days_ahead)


def _parse_barpeople_time(value: str) -> datetime_time | None:
    text = value.lower().replace(".", "").replace(" ", "")
    match = re.match(r"^(\d{1,2})(?::(\d{2}))?(am|pm)$", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)
    if hour == 12:
        hour = 0
    if meridiem == "pm":
        hour += 12
    if hour > 23 or minute > 59:
        return None
    return datetime_time(hour, minute)


def _format_barpeople_time(value: datetime_time) -> str:
    hour = value.hour
    minute = value.minute
    meridiem = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:{minute:02d} {meridiem}"


def _split_barpeople_live_detail(detail: str) -> tuple[str, str]:
    parts = _dash_parts(detail)
    if len(parts) >= 2:
        return " - ".join(parts[:-1]), parts[-1]
    return detail, ""


def _split_barpeople_bar_detail(detail: str) -> tuple[str, str]:
    parts = _dash_parts(detail)
    if len(parts) >= 2:
        return parts[0], " - ".join(parts[1:])
    return detail, ""


def _dash_parts(value: str) -> list[str]:
    normalized = re.sub(r"\s*[-–—]\s*", " - ", value)
    return [part.strip() for part in normalized.split(" - ") if part.strip()]


def _barpeople_title(category: str, performer_or_descriptor: str, venue: str) -> str:
    performer_or_descriptor = _clean_barpeople_line(performer_or_descriptor)
    venue = _clean_barpeople_line(venue)
    if category == "karaoke":
        return f"Karaoke at {venue}"
    if category == "trivia":
        return f"Trivia at {venue}"
    if category == "open mic":
        return f"Open mic at {venue}"
    if category == "dj" and not performer_or_descriptor:
        return f"DJ night at {venue}"
    if performer_or_descriptor:
        return f"{performer_or_descriptor} at {venue}"
    return f"{category.title()} at {venue}"


def _barpeople_category(activity: str, detail: str) -> str:
    text = f"{activity} {detail}".lower()
    if "trivia" in text:
        return "trivia"
    if "karaoke" in text:
        return "karaoke"
    if "open mic" in text or "open-mic" in text:
        return "open mic"
    if "dj" in text:
        return "dj"
    if "music" in text or activity == "live music":
        return "live music"
    return "bar event"


def _barpeople_activity_heading(line: str) -> str | None:
    lower = line.lower().strip(":")
    if lower in {"karaoke", "open mic", "trivia"}:
        return lower
    return None


def _barpeople_weekday(line: str) -> int | None:
    lower = line.lower().strip(" :")
    lower = lower.removeprefix("every ").strip()
    return WEEKDAYS.get(lower)


def _barpeople_area_heading(line: str) -> str | None:
    stripped = line.strip()
    if not stripped.endswith(":"):
        return None
    label = stripped[:-1].strip()
    if "including" in label.lower():
        return None
    if _barpeople_weekday(label) is not None:
        return None
    if len(label) > 45 or not re.search(r"[A-Za-z]", label):
        return None
    if label.upper() == label:
        return _title_area(label)
    return None


def _parenthetical_area(line: str) -> str:
    matches = re.findall(r"\(([^()]{2,45})\)", line)
    return _title_area(matches[-1]) if matches else ""


def _strip_parenthetical_area(line: str) -> str:
    return re.sub(r"\s*\([^()]{2,45}\)\s*$", "", line).strip(" -")


def _looks_like_barpeople_area(line: str) -> bool:
    lower = line.lower()
    return lower in {
        "saratoga springs",
        "albany",
        "troy",
        "schenectady",
        "clifton park",
        "lake george",
        "glens falls",
        "capital region",
    }


def _looks_like_barpeople_venue(line: str) -> bool:
    lower = line.lower()
    if len(line) > 50 or len(line) < 3:
        return False
    blocked = {"live music", "dj events", "bar events", "other events & locations", "events", "contact us"}
    return lower not in blocked and not TIME_RE.search(line) and "weekly" not in lower and "schedule" not in lower


def _title_area(value: str) -> str:
    words = str(value or "").replace("VO0R", "Voor").replace("LOUDONVILLE", "Loudonville")
    return " ".join(part.capitalize() if not part.isupper() else part.title() for part in words.split())


def _clean_barpeople_line(value: str) -> str:
    value = re.sub(r"[\u200b-\u200f\u202a-\u202e]", "", str(value or ""))
    value = value.replace("—", "-").replace("–", "-")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _dedupe_events(events: List[Dict]) -> List[Dict]:
    result: list[Dict] = []
    seen: set[str] = set()
    for event in events:
        key = _stable_id(event.get("title", ""), event.get("date", ""), event.get("venue", ""), event.get("location", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result


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
                        "ticket_url": item.get("ticket_url") or item.get("url"),
                        "ticket_status": item.get("ticket_status", "event site"),
                    }
                    if "price_note" in item:
                        event["price_note"] = item["price_note"]
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
