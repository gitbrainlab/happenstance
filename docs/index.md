# Happenstance Documentation

## Overview

**Happenstance** is a scheduled data aggregation and static publishing application that creates a weekend planner for restaurants and events. The application fetches data from various sources, intelligently pairs restaurants with events, and publishes everything as a static website on GitHub Pages.

### What It Produces

The application generates:

1. **Static JSON Data Files** (`docs/*.json`)
   - `restaurants.json` - Restaurant listings with cuisine, address, and ratings
   - `events.json` - Upcoming events with categories, dates, and locations
   - `meta.json` - Metadata including pairings (restaurant + event combinations)
   - `config.json` - UI configuration and branding

2. **Static Website** (served from `docs/`)
   - Interactive single-page application
   - Multiple views: Restaurants, Events, and Paired recommendations
   - Filtering and layout options (card/table view)
   - Dark theme UI with responsive design

3. **Automated Deployments**
   - Daily scheduled updates (6 AM UTC)
   - Automatic deployment on every push to `main`
   - Published to GitHub Pages

### How It's Delivered

The application uses a **static site architecture**:

- **Build Time**: Data aggregation runs via GitHub Actions (or locally)
- **Runtime**: Static files served via GitHub Pages CDN
- **No Backend**: Everything is pre-generated JSON and HTML/CSS/JS
- **Zero Cost**: Fully hosted on GitHub's free tier

## Key Folders

### 📁 `happenstance/` - Generator (Python)

The core data aggregation engine written in Python 3.11+.

**Key Files:**
- `cli.py` - Command-line interface (`aggregate`, `serve` commands)
- `aggregate.py` - Main orchestration: fetches data, builds pairings, generates JSON
- `sources.py` - API integrations (Google Places, Ticketmaster, Eventbrite, AI)
- `pairing.py` - Intelligent restaurant-event matching algorithm
- `config.py` - Configuration loader (profiles, data sources)
- `validate.py` - Data validation and filtering utilities
- `hash.py` - Content hashing for change detection

**What It Does:**
1. Loads configuration from `config/config_logic.json`
2. Fetches restaurant and event data from configured sources
3. Geocodes locations and calculates distances
4. Generates intelligent pairings based on proximity and compatibility
5. Writes JSON files to `docs/` directory

### 📁 `docs/` - Output & Frontend

Contains both generated data files and the static website.

**Generated Data (built by generator):**
- `restaurants.json` - ~12KB
- `events.json` - ~4KB
- `meta.json` - ~9KB (includes pairings)
- `config.json` - ~400B

**Static Website Files:**
- `index.html` - Single-page application structure
- `app.js` - Client-side JavaScript (data loading, filtering, rendering)
- `styles.css` - Dark theme styling
- `CNAME` - Custom domain configuration (optional)

**Supporting Documentation:**
- `ARCHITECTURE.md` - Technical architecture details
- `API_SETUP.md` - API key setup guide
- `AI_SETUP.md` - AI-powered data setup
- `GITHUB_PAGES_SETUP.md` - Deployment guide
- `PAIRING_SYSTEM.md` - Pairing algorithm details
- `ROADMAP.md` - Future features
- `BUGS.md` - Known issues

### 📁 `config/` - Configuration

**Files:**
- `config_logic.json` - Profile definitions, data sources, API settings, branding

**What's Configured:**
- Regional profiles (default: Capital Region, NY)
- Data sources (fixtures, Google Places, Ticketmaster, AI)
- API configuration (cities, counts, search parameters)
- Branding (title, tagline, accent color)
- Pairing rules and target cuisines/categories

### 📁 `.github/workflows/` - Automation

GitHub Actions workflows for CI/CD:

**Workflows:**
- `pages.yml` - Builds and deploys to GitHub Pages (daily + on push)
- `validate-pages.yml` - Validates published JSON endpoints
- `ci.yml` - Continuous integration (tests, linting)

**Deployment Process:**
1. Checkout repository
2. Install Python dependencies
3. Run `python -m happenstance.cli aggregate` with API keys from secrets
4. Upload `docs/` directory as GitHub Pages artifact
5. Deploy to GitHub Pages

### 📁 `tests/` - Test Suite

Python tests for the generator:

**Test Files:**
- `test_aggregate.py` - Data aggregation pipeline tests
- `test_pairing.py` - Pairing algorithm tests
- `test_contracts.py` - JSON schema validation
- `test_sources.py` - API integration tests
- `test_validate.py` - Data validation tests
- `test_hash.py` - Content hashing tests

**E2E Tests:**
- `tests/e2e/` - Playwright browser tests for the UI

### 📁 `scripts/` - Utilities

Helper scripts for development and testing:

- `demo_pairing.py` - Demonstrate pairing logic
- `fetch_ai_data.py` - AI-powered data fetching
- `generate_real_data.py` - Generate data from real APIs
- `integration_example.py` - Integration examples

## Data Flow

```
┌─────────────────────────────────────────────┐
│  Data Sources (APIs or Fixtures)            │
│  - Google Places (restaurants)              │
│  - Ticketmaster/Eventbrite (events)         │
│  - AI-powered search (alternative)          │
│  - Fixture data (fallback/demo)             │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Python Generator (happenstance/)           │
│  1. Fetch data from sources                 │
│  2. Normalize and validate                  │
│  3. Geocode locations                       │
│  4. Calculate pairings                      │
│  5. Generate JSON files                     │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  Static Files (docs/)                       │
│  - *.json (data)                            │
│  - index.html, app.js, styles.css (UI)     │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  GitHub Pages Deployment                    │
│  - Automatic daily updates                  │
│  - CDN distribution                         │
│  - HTTPS enforced                           │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  User's Browser                             │
│  - Loads static files                       │
│  - Renders interactive UI                   │
│  - No backend required                      │
└─────────────────────────────────────────────┘
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Generate data (uses fixture/demo data by default)
python -m happenstance.cli aggregate

# Serve locally
python -m happenstance.cli serve
# or
make dev

# Open browser to http://localhost:8000
```

### With Real Data

```bash
# Set up API keys (see docs/API_SETUP.md)
export GOOGLE_PLACES_API_KEY="your_key"
export TICKETMASTER_API_KEY="your_key"

# Generate with real data
python -m happenstance.cli aggregate
```

## Next Steps

- **[Generator Documentation](generator.md)** - CLI usage, configuration, adding data sources
- **[Deployment Guide](deployment.md)** - GitHub Pages setup and custom domains
- **[Architecture Details](ARCHITECTURE.md)** - Technical deep dive
- **[API Setup](API_SETUP.md)** - Configure real data sources

## Project Philosophy

1. **Reproducible**: Clear data lineage from source to JSON
2. **Resilient**: Automatic fallback to fixture data
3. **Transparent**: Scheduled runs with visible logs and artifacts
4. **Free**: No paid services required for basic functionality
5. **Simple**: Minimal dependencies, straightforward architecture
