# API Keys Setup Guide

This guide explains how to set up API keys to fetch real restaurant and event data.

## Overview

The Happenstance app can fetch data from:
- **Google Places API** for restaurants
- **Google Programmable Search** for dated event pages with structured metadata (requires Search Engine ID)
- **Ticketmaster API** for events
- **Eventbrite API** for events (alternative)
- **Grok API** for AI-powered search (alternative)
- **OpenAI API** for AI-powered search (alternative)

Without API keys, the system automatically falls back to demo/fixture data.

## Setting Up API Keys

### 1. Google Places API (Restaurants)

**Get your API key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Places API" 
4. Create credentials → API Key
5. (Optional but recommended) Restrict the API key to Places API only

**Configure the location:**
Edit `config/config_logic.json` to set your target city:
```json
{
  "api_config": {
    "google_places": {
      "city": "San Francisco",
      "count": 20
    }
  }
}
```

### 2. Google Programmable Search (Events)

Google Places is strong for restaurants and venue enrichment, but it does not provide a dated event-listings feed. For Google-backed event discovery, Happenstance supports Programmable Search results and only imports results that expose a real event start date in structured metadata.

**Requirements:**
1. `GOOGLE_API_KEY` or `GOOGLE_PLACES_API_KEY`
2. `GOOGLE_CSE_ID` or `GOOGLE_SEARCH_ENGINE_ID`
3. Custom Search JSON API access for that Google Cloud project

**Configure event search queries:**
```json
{
  "api_config": {
    "google_search": {
      "city": "Capital Region, NY",
      "count": 80,
      "queries": [
        "event calendar Albany NY",
        "event calendar Saratoga Springs NY",
        "upcoming concerts Capital Region NY"
      ]
    }
  }
}
```

### 3. Ticketmaster API (Events)

**Get your API key:**
1. Go to [Ticketmaster Developer Portal](https://developer.ticketmaster.com/)
2. Sign up for a free account
3. Create an app to get your Consumer Key (API Key)

**Configure the location:**
Edit `config/config_logic.json`:
```json
{
  "api_config": {
    "ticketmaster": {
      "city": "San Francisco",
      "count": 20
    }
  }
}
```

### 4. Eventbrite API (Alternative Events Source)

**Get your API token:**
1. Go to [Eventbrite App Management](https://www.eventbrite.com/platform/api)
2. Create an app
3. Generate a Personal OAuth token

**Configure the location:**
Edit `config/config_logic.json`:
```json
{
  "api_config": {
    "eventbrite": {
      "city": "San Francisco",
      "count": 20
    }
  }
}
```

### 5. Grok API (AI-Powered Search)

**Get your API key:**
1. Go to [x.ai API](https://x.ai/api)
2. Sign up and get your API key

**Note:** Requires implementing AI search functionality that calls Grok API directly.

### 6. OpenAI API (AI-Powered Search)

**Get your API key:**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up and create an API key

**Note:** Requires implementing AI search functionality that calls OpenAI API directly.

## Local Development

1. Copy `.env.example` to `.env`
2. Add your API keys:
```bash
GOOGLE_PLACES_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_google_programmable_search_engine_id_here
TICKETMASTER_API_KEY=your_ticketmaster_api_key_here
EVENTBRITE_API_KEY=your_eventbrite_token_here
GROK_API_KEY=your_grok_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

3. Run the aggregator:
```bash
python -m happenstance.cli aggregate
```

## GitHub Actions Setup

To use real data in GitHub Pages deployments:

1. Go to your repository Settings
2. Navigate to "Secrets and variables" → "Actions"
3. Add the following repository secrets:
   - `GOOGLE_PLACES_API_KEY`
   - `GOOGLE_CSE_ID` (optional, enables Google-backed event discovery)
   - `TICKETMASTER_API_KEY`
   - `EVENTBRITE_API_KEY`
   - `GROK_API_KEY` (for AI-powered search)
   - `OPENAI_API_KEY` (for AI-powered search)

The workflow (`.github/workflows/pages.yml`) is already configured to use these secrets.

## Choosing Data Sources

Edit `config/config_logic.json` to select which sources to use:

```json
{
  "data_sources": {
    "restaurants": "google_places",  // Options: "fixtures", "google_places", "ai"
    "events": "ticketmaster"         // Options: "fixtures", "ticketmaster", "eventbrite", "google_search", "ai"
  }
}
```

## Troubleshooting

### "API key not provided" warnings
- The system is falling back to fixture data
- Add the appropriate API key environment variable

### "Failed to fetch from API" errors
- Check that your API key is valid
- Verify the API is enabled (for Google)
- Check your API usage limits
- The system will automatically fall back to fixture data

### No data appearing
- Check `EVENT_WINDOW_DAYS` is set appropriately (default: 14 days)
- Verify your location configuration matches your API settings
- Check API rate limits haven't been exceeded

## API Rate Limits

Be aware of rate limits:
- **Google Places**: 
  - Free tier: Limited requests per day
  - See [pricing](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing)

- **Google Programmable Search**:
  - Requires API key plus Search Engine ID
  - Query limits and availability depend on the Google Custom Search JSON API status for your project

- **Ticketmaster**: 
  - Free tier: 5,000 requests per day, 5 requests per second
  - See [rate limits](https://developer.ticketmaster.com/products-and-docs/apis/getting-started/#rate-limit)

- **Eventbrite**: 
  - Varies by plan
  - See [rate limits](https://www.eventbrite.com/platform/api#/introduction/rate-limits)

## Cost Considerations

- **Google Places**: Pay-per-use after free tier
- **Ticketmaster**: Free for standard Discovery API
- **Eventbrite**: Free for basic access

For the scheduled daily GitHub Actions run, typical usage should stay within free tiers.
