# Happenstance

**Static weekend planner for restaurants and events.** Aggregates data from multiple sources, pairs restaurants with events intelligently, and publishes as a static website on GitHub Pages.

## 🌐 Live Demo

**[View the live app →](https://evcatalyst.github.io/happenstance/)**

Browse restaurants, events, and paired recommendations with filtering and multiple layout options:
- **Restaurants tab**: Dining options filtered by cuisine or keywords
- **Events tab**: Upcoming events by category (art, music, family, sports)
- **Paired tab**: Recommended restaurant + event combinations
- **Filter**: Search by keywords or categories
- **Layout**: Toggle between card view (visual) and table view (compact)

## 📚 Documentation

- **[Getting Started](docs/index.md)** - Overview, key folders, and data flow
- **[Generator Guide](docs/generator.md)** - CLI usage, configuration, and adding data sources
- **[Deployment Guide](docs/deployment.md)** - GitHub Pages setup, custom domains, and validation
- **[API Setup](docs/API_SETUP.md)** - Configure real data sources (Google Places, Ticketmaster)
- **[Architecture](docs/ARCHITECTURE.md)** - Technical deep dive
- **[Roadmap](docs/ROADMAP.md)** - Feature roadmap and future plans

## 🚀 Run Locally

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/gitbrainlab/happenstance.git
cd happenstance

# Install dependencies
pip install -r requirements.txt

# Generate data (uses demo/fixture data by default - no API keys needed!)
python -m happenstance.cli aggregate

# Start local server
python -m happenstance.cli serve
# Or use Makefile shortcut
make dev
```

**Open your browser to http://localhost:8000**

### No-API-Key Demo Mode

By default, Happenstance uses **fixture data** (sample restaurants and events) so you can try it immediately without any API keys or paid services. This is perfect for:
- Testing the application
- Development and customization
- Understanding how it works before connecting to real data sources

The fixture data is configured in `config/config_logic.json`:
```json
{
  "data_sources": {
    "restaurants": "fixtures",
    "events": "fixtures"
  }
}
```

### Using Real Data (Optional)

To fetch real restaurant and event data:

1. Get API keys (see [docs/API_SETUP.md](docs/API_SETUP.md) for details):
   - **Google Places API** - for restaurants
   - **Ticketmaster API** - for events
   - Both have free tiers!

2. Set environment variables:
   ```bash
   export GOOGLE_PLACES_API_KEY="your_google_key"
   export TICKETMASTER_API_KEY="your_ticketmaster_key"
   ```

3. Update `config/config_logic.json`:
   ```json
   {
     "data_sources": {
       "restaurants": "google_places",
       "events": "ticketmaster"
     }
   }
   ```

4. Generate fresh data:
   ```bash
   python -m happenstance.cli aggregate
   ```

**Alternative:** Use AI-powered data sources (Grok/OpenAI) - see [docs/AI_SETUP.md](docs/AI_SETUP.md)

### Configuration

Edit `config/config_logic.json` to customize:
- **Region**: Your city/area (e.g., "San Francisco", "New York City")
- **Branding**: Site title, tagline, and accent color
- **Data sources**: Fixtures, APIs, or AI
- **Cuisines**: Preferred restaurant types
- **Categories**: Preferred event types

Environment variable overrides:
```bash
export PROFILE=default              # Profile to use from config
export EVENT_WINDOW_DAYS=14         # Days ahead for events
export BASE_URL=http://localhost:8000
```

## 🔧 Deploy Your Fork

### Step 1: Fork the Repository

Click the **Fork** button at the top of this page to create your own copy.

### Step 2: Customize Configuration

Edit `config/config_logic.json` in your fork:

```json
{
  "profiles": {
    "default": {
      "region": "Your City, State",
      "branding": {
        "title": "Happenstance - Your City",
        "tagline": "Plan your weekend with great food and events",
        "accent_color": "#3b82f6"
      },
      "data_sources": {
        "restaurants": "fixtures",
        "events": "fixtures"
      }
    }
  }
}
```

**Tip:** Start with fixtures, then add API keys later for real data.

### Step 3: Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under "Build and deployment":
   - Source: **GitHub Actions**
3. Under "Workflow permissions" (Settings → Actions → General):
   - Select **"Read and write permissions"**
   - Save

### Step 4: Add API Keys (Optional)

For real data, add repository secrets:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Add secrets:
   - `GOOGLE_PLACES_API_KEY` - for restaurants
   - `TICKETMASTER_API_KEY` - for events

See [docs/API_SETUP.md](docs/API_SETUP.md) for obtaining API keys (both have free tiers).

### Step 5: Deploy

**Option A: Push to trigger deployment**
```bash
git add config/config_logic.json
git commit -m "Configure for my city"
git push origin main
```

**Option B: Manual trigger**
1. Go to **Actions** tab
2. Click **"Pages Deploy"**
3. Click **"Run workflow"**

### Step 6: Access Your Site

After 2-3 minutes, your site will be live at:
```
https://yourusername.github.io/happenstance/
```

Check **Settings** → **Pages** for the URL.

### Validating Scheduled Runs

Your site automatically updates daily at 6 AM UTC. Validation ensures data is being refreshed correctly and your site remains functional.

**Why validate?** Scheduled runs can fail due to API rate limits, configuration errors, or GitHub Actions issues. Regular validation helps you catch problems early.

**Check GitHub Actions:**
1. Go to **Actions** tab
2. Look for runs with 🕐 clock icon (scheduled)
3. View logs to see data generation output

**Check deployment history:**
1. **Settings** → **Pages**
2. View deployment timestamps - should show daily updates

**Check site footer:**
Visit your site and check the bottom for the update timestamp:
```
Data from Your City • Updated: 2025-12-29 at 06:05 UTC
```

**Check JSON metadata:**
```bash
curl https://yourusername.github.io/happenstance/meta.json | grep generated_at
```

**Common issues and solutions:**
- **No scheduled runs**: GitHub may pause workflows on inactive repos - trigger manually once to reactivate
- **Run failed**: Check logs - usually API limits or errors (fixture fallback ensures site still works)
- **Data unchanged**: Check `_meta.changed` field - if `false`, no updates were needed (this is normal)
- **If validation fails**: See the detailed troubleshooting guide in [docs/deployment.md](docs/deployment.md)

See [docs/deployment.md](docs/deployment.md) for detailed deployment documentation, custom domains, and troubleshooting.

## 🧪 Testing

```bash
# Linting
ruff check .
# or
make lint

# Unit and contract tests
pytest
# or
make test

# End-to-end tests (requires Playwright)
npx playwright install --with-deps chromium
npm run test:e2e
# or
make e2e
```

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork the repository** and create a feature branch
2. **Make your changes** - follow existing code style
3. **Add tests** for new functionality
4. **Run tests** to ensure nothing breaks:
   ```bash
   make lint
   make test
   ```
5. **Submit a pull request** with a clear description

### Development Guidelines

- **Code style**: Follow existing patterns, use type hints
- **Tests**: Add tests for new features and bug fixes
- **Documentation**: Update relevant docs in `docs/`
- **Commits**: Write clear, descriptive commit messages

### Adding New Data Sources

See [docs/generator.md](docs/generator.md#adding-a-new-data-source) for a complete guide on adding new API integrations.

### Reporting Issues

- Check [docs/BUGS.md](docs/BUGS.md) for known issues
- Search existing issues before creating new ones
- Provide clear reproduction steps
- Include logs from GitHub Actions if deployment-related

## 📖 How It Works

```
┌─────────────────────────────────┐
│  Data Sources                   │
│  - Fixtures (demo data)         │
│  - Google Places (restaurants)  │
│  - Ticketmaster (events)        │
│  - AI-powered (alternative)     │
└────────────┬────────────────────┘
             ▼
┌─────────────────────────────────┐
│  Python Generator               │
│  1. Fetch & normalize data      │
│  2. Geocode locations           │
│  3. Calculate pairings          │
│  4. Generate JSON files         │
└────────────┬────────────────────┘
             ▼
┌─────────────────────────────────┐
│  Static Files (docs/)           │
│  - restaurants.json             │
│  - events.json                  │
│  - meta.json (with pairings)    │
│  - index.html + app.js          │
└────────────┬────────────────────┘
             ▼
┌─────────────────────────────────┐
│  GitHub Pages                   │
│  - Automatic daily updates      │
│  - CDN distribution             │
│  - Free hosting                 │
└─────────────────────────────────┘
```

**Key Features:**
- **Reproducible**: Clear data lineage from source to output
- **Resilient**: Automatic fallback to fixture data
- **Free**: No paid services required (uses free API tiers)
- **Simple**: Static site architecture, no backend needed
- **Automated**: Daily scheduled updates via GitHub Actions

## 📄 License

This project is open source. See the repository for license details.

## 🙏 Acknowledgments

- Data sources: Google Places API, Ticketmaster API
- Geocoding: OpenStreetMap Nominatim
- Hosting: GitHub Pages
- Automation: GitHub Actions
