# Generator Documentation

## Overview

The generator is a Python CLI application that aggregates restaurant and event data from various sources, performs intelligent pairing, and outputs static JSON files for the web application.

## CLI Usage

### Installation

```bash
# Clone the repository
git clone https://github.com/gitbrainlab/happenstance.git
cd happenstance

# Install dependencies
pip install -r requirements.txt
```

### Commands

#### `aggregate` - Generate Data Files

Fetches data from configured sources and generates JSON files in `docs/`.

```bash
# Basic usage (uses default profile)
python -m happenstance.cli aggregate

# With specific profile
python -m happenstance.cli aggregate --profile default

# Or use Makefile
make aggregate
```

**What it does:**
1. Loads configuration from `config/config_logic.json`
2. Fetches restaurants from configured source (Google Places, AI, or fixtures)
3. Fetches events from configured source (Ticketmaster, Eventbrite, AI, or fixtures)
4. Filters events by date window (default: next 14 days)
5. Geocodes event venues using OpenStreetMap Nominatim
6. Calculates distances between events and restaurants
7. Generates intelligent pairings based on proximity and compatibility
8. Writes JSON files to `docs/`:
   - `restaurants.json`
   - `events.json`
   - `meta.json`
   - `config.json`

**Output:**
```
Using fixture data for restaurants in Capital Region, NY
Using fixture data for events in Capital Region, NY
Generated 4 restaurants, 4 events, 4 pairings
```

#### `serve` - Local Development Server

Serves the `docs/` directory on a local HTTP server for development and testing.

```bash
# Basic usage (serves on port 8000)
python -m happenstance.cli serve

# Custom port
python -m happenstance.cli serve --port 3000

# Custom directory
python -m happenstance.cli serve --directory ./docs

# Or use Makefile (runs aggregate first, then serves)
make dev
```

**Access:** Open http://localhost:8000 in your browser

## Configuration

### Profile System

Profiles are defined in `config/config_logic.json` and allow different configurations for different regions or deployment scenarios.

**Structure:**
```json
{
  "profiles": {
    "default": {
      "region": "Capital Region, NY",
      "branding": { ... },
      "data_sources": { ... },
      "api_config": { ... },
      "target_cuisines": [ ... ],
      "target_categories": [ ... ]
    },
    "custom_profile": { ... }
  }
}
```

### Configuration Options

#### Region & Branding

```json
{
  "region": "Capital Region, NY",
  "branding": {
    "title": "Happenstance - Capital Region",
    "tagline": "Plan your weekend with great food and events",
    "accent_color": "#3b82f6"
  }
}
```

- `region` - Geographic region for data fetching
- `branding.title` - Displayed in UI header
- `branding.tagline` - Subtitle in UI
- `branding.accent_color` - CSS color for UI accents

#### Data Sources

```json
{
  "data_sources": {
    "restaurants": "fixtures",
    "events": "fixtures"
  }
}
```

**Restaurant Sources:**
- `"fixtures"` - Demo/sample data (no API key needed) **[DEFAULT]**
- `"google_places"` - Google Places API
- `"ai"` - AI-powered search (Grok or OpenAI)

**Event Sources:**
- `"fixtures"` - Demo/sample data (no API key needed) **[DEFAULT]**
- `"ticketmaster"` - Ticketmaster API
- `"eventbrite"` - Eventbrite API
- `"ai"` - AI-powered search (Grok or OpenAI)

#### API Configuration

```json
{
  "api_config": {
    "google_places": {
      "city": "San Francisco",
      "count": 20
    },
    "ticketmaster": {
      "city": "San Francisco",
      "count": 20
    },
    "eventbrite": {
      "city": "San Francisco",
      "count": 20
    },
    "ai": {
      "city": "Niskayuna, NY",
      "restaurant_count": 35,
      "event_count": 30
    }
  }
}
```

- `city` - Target city for API searches
- `count` / `restaurant_count` / `event_count` - Number of results to fetch

#### Pairing Rules

```json
{
  "pairing_rules": [
    "Pair live music with vibrant, shareable plates.",
    "Match family-friendly events with comforting classics.",
    "Keep late-night shows close to late-night kitchens."
  ]
}
```

Displayed in the UI to explain pairing logic to users.

#### Target Filters

```json
{
  "target_cuisines": ["Italian", "Sushi", "BBQ", "Vegan", "Mexican", "Thai"],
  "target_categories": ["live music", "art", "family", "sports"]
}
```

- `target_cuisines` - Preferred restaurant cuisines
- `target_categories` - Preferred event categories

**Note:** These are hints, not hard filters. The generator will fetch matching data when available.

### Environment Variables

Override configuration via environment variables:

```bash
# Profile selection
export PROFILE=default

# Event filtering
export EVENT_WINDOW_DAYS=14

# Search mode
export LIVE_SEARCH_MODE=local

# Base URL (for local testing)
export BASE_URL=http://localhost:8000

# Commit behavior
export COMMIT_DATA=0  # 0 = artifact-only, 1 = commit JSON changes

# Port for local server
export PORT=8000
```

### API Keys (Environment Variables)

See [API_SETUP.md](API_SETUP.md) for detailed setup instructions.

```bash
# Google Places API
export GOOGLE_PLACES_API_KEY="your_key_here"

# Ticketmaster API
export TICKETMASTER_API_KEY="your_key_here"

# Eventbrite API
export EVENTBRITE_API_KEY="your_key_here"

# AI APIs (optional)
export GROK_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"

# AI data as JSON strings (optional)
export AI_RESTAURANTS_DATA='[{"name": "...", ...}]'
export AI_EVENTS_DATA='[{"title": "...", ...}]'
```

**Fallback Behavior:**
If API keys are not provided, the generator automatically falls back to fixture data.

## Output Schema

### `restaurants.json`

Array of restaurant objects with metadata sentinel.

```json
[
  {
    "name": "Blue Harbor Grill",
    "cuisine": "Seafood",
    "address": "Capital Region, NY Waterfront",
    "url": "https://example.com/blue-harbor",
    "match_reason": "Great before a waterfront concert",
    "rating": 4.7,
    "price_level": 2
  },
  {
    "_meta": {
      "hash": "abc123...",
      "item_count": 4,
      "changed": false
    }
  }
]
```

**Fields:**
- `name` (required) - Restaurant name
- `cuisine` (required) - Cuisine type (e.g., "Italian", "Sushi")
- `address` (required) - Full address or location
- `url` (required) - Link to restaurant (Google Maps, website, etc.)
- `match_reason` (optional) - Why this restaurant is recommended
- `rating` (optional) - Star rating (0-5)
- `price_level` (optional) - Price tier (0-4)

**Metadata Sentinel:**
The last element is always `_meta` with:
- `hash` - SHA-256 hash of canonical JSON
- `item_count` - Number of items (excluding metadata)
- `changed` - Whether content changed since last generation

### `events.json`

Array of event objects with metadata sentinel.

```json
[
  {
    "title": "Waterfront Jazz Night",
    "category": "live music",
    "date": "2025-12-31T19:00:00+00:00",
    "location": "Capital Region, NY Waterfront Stage",
    "url": "https://example.com/jazz-night",
    "description": "Evening jazz performance"
  },
  {
    "_meta": {
      "hash": "def456...",
      "item_count": 4,
      "changed": false
    }
  }
]
```

**Fields:**
- `title` (required) - Event name
- `category` (required) - Event type (e.g., "live music", "art", "sports", "family")
- `date` (required) - ISO 8601 timestamp
- `location` (required) - Venue name and address
- `url` (required) - Link to event details
- `description` (optional) - Event description

**Date Filtering:**
Events are automatically filtered to include only those within `EVENT_WINDOW_DAYS` (default: 14 days from now).

### `meta.json`

Metadata and pairings.

```json
{
  "generated_at": "2025-12-29T15:20:00+00:00",
  "profile": "default",
  "region": "Capital Region, NY",
  "branding": {
    "title": "Happenstance - Capital Region",
    "tagline": "Plan your weekend with great food and events",
    "accent_color": "#3b82f6"
  },
  "pairing_rules": [
    "Pair live music with vibrant, shareable plates."
  ],
  "search": {
    "mode": "local",
    "radius_km": 40,
    "limit": 10
  },
  "gap_bullets": [],
  "events": {
    "hash": "def456...",
    "item_count": 4,
    "changed": false
  },
  "restaurants": {
    "hash": "abc123...",
    "item_count": 4,
    "changed": false
  },
  "pairings": [
    {
      "event": "Waterfront Jazz Night",
      "restaurant": "Blue Harbor Grill",
      "match_reason": "Located in capital region, ny; 0.3 mi - walking distance; Seafood pairs well with live music",
      "event_url": "https://example.com/jazz-night",
      "restaurant_url": "https://example.com/blue-harbor",
      "event_date": "2025-12-31T19:00:00+00:00",
      "event_location": "Capital Region, NY Waterfront Stage",
      "distance_miles": 0.3,
      "nearby_restaurants": [
        {
          "name": "Harbor View Cafe",
          "cuisine": "American",
          "url": "https://maps.google.com/...",
          "rating": 4.5
        }
      ]
    }
  ],
  "guidance": "Events span December 2025"
}
```

**Key Fields:**
- `generated_at` - Timestamp of generation
- `profile` - Active configuration profile
- `region` - Geographic region
- `branding` - UI branding configuration
- `pairing_rules` - Pairing guidance for users
- `pairings` - Array of restaurant-event combinations with:
  - `event` - Event title
  - `restaurant` - Restaurant name
  - `match_reason` - Explanation of why they pair well
  - `distance_miles` - Distance between venue and restaurant (if available)
  - `nearby_restaurants` - Alternative nearby options

### `config.json`

UI configuration only (subset of meta.json).

```json
{
  "branding": {
    "title": "Happenstance - Capital Region",
    "tagline": "Plan your weekend with great food and events",
    "accent_color": "#3b82f6"
  },
  "pairing_rules": [
    "Pair live music with vibrant, shareable plates."
  ]
}
```

## Adding a New Data Source

### Pattern

To add a new data source adapter, follow this pattern:

1. **Create a fetcher function** in `happenstance/sources.py`
2. **Normalize the data** to the standard schema
3. **Register the source** in configuration
4. **Update aggregate.py** to call your fetcher
5. **Add tests** for the new source

### Example: Adding a Yelp Restaurant Source

#### Step 1: Create Fetcher Function

Add to `happenstance/sources.py`:

```python
def fetch_yelp_restaurants(
    city: str,
    region: str,
    cuisine_types: List[str] | None = None,
    count: int = 20,
) -> List[Dict]:
    """
    Fetch restaurants from Yelp API.
    
    Args:
        city: City to search in
        region: Region for fallback
        cuisine_types: Optional list of cuisine types to filter
        count: Number of results to return
        
    Returns:
        List of restaurant dictionaries
        
    Raises:
        ValueError: If API key missing or request fails
    """
    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        raise ValueError("YELP_API_KEY environment variable not set")
    
    # Make API request
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "location": city,
        "term": "restaurants",
        "limit": count,
    }
    
    data = _make_request(url, headers=headers, params=params)
    
    # Normalize to standard schema
    restaurants = []
    for business in data.get("businesses", []):
        restaurant = {
            "name": business["name"],
            "cuisine": business.get("categories", [{}])[0].get("title", "Restaurant"),
            "address": business["location"]["display_address"][0],
            "url": business["url"],
            "rating": business.get("rating", 0),
            "price_level": len(business.get("price", "$")),  # $ = 1, $$ = 2, etc.
        }
        restaurants.append(restaurant)
    
    return restaurants
```

#### Step 2: Register in Configuration

Update `config/config_logic.json`:

```json
{
  "data_sources": {
    "restaurants": "yelp"
  },
  "api_config": {
    "yelp": {
      "city": "San Francisco",
      "count": 20
    }
  }
}
```

#### Step 3: Update Aggregator

Modify `happenstance/aggregate.py` in `_fetch_restaurants()`:

```python
def _fetch_restaurants(cfg: Mapping) -> List[Dict]:
    """Fetch restaurants based on configured data source."""
    data_sources = cfg.get("data_sources", {})
    restaurant_source = data_sources.get("restaurants", "fixtures")
    region = cfg["region"]
    
    # ... existing code ...
    
    elif restaurant_source == "yelp":
        print(f"Fetching restaurants from Yelp API for {region}")
        api_config = cfg.get("api_config", {}).get("yelp", {})
        city = api_config.get("city", region)
        try:
            return fetch_yelp_restaurants(
                city=city,
                region=region,
                cuisine_types=cfg.get("target_cuisines"),
                count=api_config.get("count", 20),
            )
        except ValueError as e:
            print(f"Warning: Failed to fetch from Yelp API: {e}")
            print("Falling back to fixture data")
            return _fixture_restaurants(region)
```

#### Step 4: Add Environment Variable

Add to `.env.example`:

```bash
# Yelp API key - Get from: https://www.yelp.com/developers
YELP_API_KEY=
```

#### Step 5: Add Tests

Create `tests/test_yelp_source.py`:

```python
import os
from unittest.mock import patch, MagicMock
from happenstance.sources import fetch_yelp_restaurants


def test_fetch_yelp_restaurants():
    """Test Yelp API integration."""
    with patch.dict(os.environ, {"YELP_API_KEY": "test_key"}):
        with patch("happenstance.sources._make_request") as mock_request:
            mock_request.return_value = {
                "businesses": [
                    {
                        "name": "Test Restaurant",
                        "categories": [{"title": "Italian"}],
                        "location": {"display_address": ["123 Main St"]},
                        "url": "https://yelp.com/test",
                        "rating": 4.5,
                        "price": "$$",
                    }
                ]
            }
            
            results = fetch_yelp_restaurants("San Francisco", "SF Bay Area", count=10)
            
            assert len(results) == 1
            assert results[0]["name"] == "Test Restaurant"
            assert results[0]["cuisine"] == "Italian"
            assert results[0]["price_level"] == 2
```

### Testing Your Source

```bash
# Set API key
export YELP_API_KEY="your_key"

# Update config to use yelp
# Edit config/config_logic.json

# Run generator
python -m happenstance.cli aggregate

# Verify output
cat docs/restaurants.json | python -m json.tool
```

## Data Caching and Refresh

### Content Hashing

The generator uses SHA-256 hashing to detect data changes:

1. Generates canonical JSON (sorted keys, no whitespace)
2. Computes hash for current data
3. Compares with previous hash from `_meta`
4. Sets `changed` flag if content differs

**Purpose:**
- Avoid unnecessary deployments when data hasn't changed
- Track data freshness in UI
- Audit trail for data updates

### Force Refresh

To force regeneration regardless of cache:

```bash
# Simply run aggregate command
python -m happenstance.cli aggregate

# The command always fetches fresh data
# Caching only affects the 'changed' flag in metadata
```

### Scheduled Updates

GitHub Actions runs the generator daily at 6 AM UTC:

```yaml
# .github/workflows/pages.yml
schedule:
  - cron: "0 6 * * *"
```

**To change the schedule:**
1. Edit `.github/workflows/pages.yml`
2. Update the cron expression
3. Commit and push

**Cron syntax:**
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6)
│ │ │ │ │
0 6 * * *
```

Example schedules:
- `0 6 * * *` - Daily at 6 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 6 * * 1` - Every Monday at 6 AM UTC
- `0 6 1,15 * *` - 1st and 15th of month at 6 AM UTC

## Validation

### Local Testing

```bash
# Run linter
ruff check .
# or
make lint

# Run unit tests
pytest
# or
make test

# Run E2E tests (requires Playwright)
npx playwright install --with-deps chromium
npm run test:e2e
# or
make e2e
```

### Schema Validation

The test suite includes contract tests that validate output JSON:

```python
# tests/test_contracts.py
def test_restaurants_json_schema(restaurants):
    """Validate restaurants.json structure."""
    assert isinstance(restaurants, list)
    assert len(restaurants) > 0
    
    for restaurant in restaurants[:-1]:  # Exclude _meta
        assert "name" in restaurant
        assert "cuisine" in restaurant
        assert "url" in restaurant
```

### Deployment Validation

After GitHub Pages deployment, the validation workflow checks:

1. **Endpoint Accessibility**: All JSON files return HTTP 200
2. **Valid JSON**: Files parse correctly
3. **Schema Compliance**: Required fields present
4. **Data Readiness**: UI sets `data-hs-ready="1"` on body

View validation results:
- Go to Actions tab in GitHub
- Check "Validate Published JSON" workflow runs

## Troubleshooting

### Common Issues

**Empty output:**
```bash
# Check EVENT_WINDOW_DAYS is large enough
export EVENT_WINDOW_DAYS=30
python -m happenstance.cli aggregate
```

**API errors:**
```bash
# Verify API keys are set
echo $GOOGLE_PLACES_API_KEY
echo $TICKETMASTER_API_KEY

# Check API quotas/limits in provider dashboards
# Generator will fallback to fixtures automatically
```

**No pairings generated:**
```bash
# Ensure both restaurants and events have data
cat docs/restaurants.json | python -m json.tool
cat docs/events.json | python -m json.tool

# Check geocoding isn't failing
# Errors appear in console during aggregate
```

**Serve command not working:**
```bash
# Ensure docs/ directory exists and has index.html
ls -la docs/

# Try explicit directory
python -m happenstance.cli serve --directory ./docs --port 8000
```

### Debug Mode

Enable detailed output:

```bash
# Python will show full tracebacks
python -m happenstance.cli aggregate

# Check specific module
python -c "from happenstance.sources import fetch_google_places_restaurants; print(fetch_google_places_restaurants.__doc__)"
```

### Getting Help

1. Check existing documentation in `docs/`
2. Review test files for usage examples
3. Check GitHub Issues for known problems
4. Review GitHub Actions logs for deployment issues
