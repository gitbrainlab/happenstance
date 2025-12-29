# Deployment Documentation

## Overview

Happenstance deploys as a static site to GitHub Pages with automated builds via GitHub Actions. This document covers setup, configuration, and troubleshooting for deployments.

## GitHub Pages Setup

### Initial Setup (New Fork/Repository)

#### Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages** (in sidebar)
3. Under "Build and deployment":
   - **Source**: Select "GitHub Actions"
   - This replaces the legacy "Deploy from branch" method

**Note:** The repository already includes the necessary workflow file (`.github/workflows/pages.yml`), so no additional configuration is needed.

#### Step 2: Configure Repository Permissions

Ensure the workflow has the necessary permissions:

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions":
   - Select **"Read and write permissions"**
   - Check **"Allow GitHub Actions to create and approve pull requests"**
3. Click **Save**

#### Step 3: Add API Keys (Optional)

To fetch real data instead of fixtures:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Add secrets (one at a time):

**For Google Places + Ticketmaster:**
```
Name: GOOGLE_PLACES_API_KEY
Secret: your_google_api_key_here

Name: TICKETMASTER_API_KEY
Secret: your_ticketmaster_api_key_here
```

**For AI-powered data (alternative):**
```
Name: GROK_API_KEY
Secret: your_grok_api_key_here

Name: OPENAI_API_KEY
Secret: your_openai_api_key_here
```

**For pre-generated AI data (alternative):**
```
Name: AI_RESTAURANTS_DATA
Secret: [{"name": "Restaurant", "cuisine": "Italian", ...}]

Name: AI_EVENTS_DATA
Secret: [{"title": "Event", "category": "music", ...}]
```

See [API_SETUP.md](API_SETUP.md) for detailed instructions on obtaining API keys.

#### Step 4: Configure Data Sources

Edit `config/config_logic.json` to specify your data sources and region:

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

**Data source options:**
- `"fixtures"` - Demo data (no API keys needed)
- `"google_places"` - Google Places API (requires API key)
- `"ticketmaster"` - Ticketmaster API (requires API key)
- `"eventbrite"` - Eventbrite API (requires API key)
- `"ai"` - AI-powered search (requires Grok or OpenAI key)

#### Step 5: Trigger First Deployment

**Option A: Push to main branch**
```bash
git add .
git commit -m "Configure for my city"
git push origin main
```

**Option B: Manual workflow dispatch**
1. Go to **Actions** tab
2. Click **"Pages Deploy"** workflow
3. Click **"Run workflow"** → **"Run workflow"**

#### Step 6: Verify Deployment

1. Wait 2-3 minutes for workflow to complete
2. Go to **Settings** → **Pages**
3. You'll see: **"Your site is live at https://username.github.io/repository-name/"**
4. Click the URL to view your site

### Deployment Triggers

The site automatically deploys when:

1. **Push to `main` branch** - Any commit triggers deployment
2. **Daily schedule** - Runs at 6 AM UTC (cron: `0 6 * * *`)
3. **Manual trigger** - Via GitHub Actions UI ("Run workflow" button)

**Workflow file:** `.github/workflows/pages.yml`

### Deployment Process

```
┌─────────────────────────────────────┐
│  Trigger (push/schedule/manual)     │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Checkout repository                │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Setup Python 3.11                  │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Install dependencies               │
│  (pip install -r requirements.txt)  │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Run data aggregation               │
│  (python -m happenstance.cli        │
│   aggregate)                        │
│                                     │
│  Environment variables:             │
│  - API keys from repository secrets │
│  - PROFILE=default                  │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Upload docs/ as Pages artifact     │
│  (actions/upload-pages-artifact)    │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Deploy to GitHub Pages             │
│  (actions/deploy-pages)             │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Site live at GitHub Pages URL      │
└─────────────────────────────────────┘
```

**Deployment time:** Typically 2-3 minutes

## Custom Domain Setup

### Prerequisites

- A registered domain name
- Access to DNS settings

### Setup Steps

#### Step 1: Create CNAME File

Create `docs/CNAME` with your domain:

```bash
echo "happenstance.yourdomain.com" > docs/CNAME
git add docs/CNAME
git commit -m "Add custom domain"
git push
```

**Note:** The repository already has a `CNAME` file. Edit it with your domain.

#### Step 2: Configure DNS

Add a CNAME record in your DNS provider:

**For subdomain (e.g., `happenstance.yourdomain.com`):**
```
Type: CNAME
Name: happenstance
Value: username.github.io
```

**For apex domain (e.g., `yourdomain.com`):**
```
Type: A
Name: @
Value: 185.199.108.153

Type: A
Name: @
Value: 185.199.109.153

Type: A
Name: @
Value: 185.199.110.153

Type: A
Name: @
Value: 185.199.111.153
```

**DNS providers:**
- Cloudflare: DNS → Add record
- Namecheap: Advanced DNS → Add record
- Google Domains: DNS → Custom records

#### Step 3: Configure in GitHub

1. Go to **Settings** → **Pages**
2. Under "Custom domain":
   - Enter your domain: `happenstance.yourdomain.com`
   - Click **Save**
3. Wait for DNS check (may take up to 24 hours)
4. Once verified, check **"Enforce HTTPS"**

**Note:** GitHub automatically provisions SSL certificate via Let's Encrypt.

#### Step 4: Verify

```bash
# Check DNS propagation
dig happenstance.yourdomain.com

# Should show:
# happenstance.yourdomain.com. 3600 IN CNAME username.github.io.
```

Visit your custom domain - it should redirect to HTTPS automatically.

### Custom Domain Considerations

**Advantages:**
- Professional branding
- Memorable URL
- Full control over domain

**Considerations:**
- DNS propagation takes 1-24 hours
- SSL certificate provisioning takes a few minutes
- Domain registration costs ~$10-20/year
- Requires DNS management knowledge

**Free alternatives:**
- Use default GitHub Pages URL: `username.github.io/repository-name`
- Perfectly functional, just longer URL

## Monitoring Deployments

### GitHub Actions Dashboard

View deployment status:

1. Go to **Actions** tab
2. Click on a workflow run
3. Expand steps to see logs

**Successful deployment:**
```
✓ Checkout repository
✓ Setup Python
✓ Install dependencies
✓ Generate data using real APIs
✓ Upload artifact
✓ Deploy to GitHub Pages
```

**Failed deployment:**
Red X on any step - click to see error logs.

### Validation Workflow

After deployment, a separate validation workflow runs:

**Workflow:** `.github/workflows/validate-pages.yml`

**What it checks:**
1. All JSON endpoints return HTTP 200
2. JSON files parse correctly
3. Required fields present in data
4. Metadata sentinel present
5. UI readiness signal (`data-hs-ready="1"`)

**To view results:**
1. Go to **Actions** tab
2. Click **"Validate Published JSON"** workflow
3. View latest run

### Logs and Artifacts

**Deployment logs:**
- Available in GitHub Actions for 90 days
- Click on workflow run → View logs
- Shows aggregation output, API calls, errors

**Build artifacts:**
- Uploaded as GitHub Pages artifact
- Automatically deployed
- Not directly downloadable (use `git checkout` of docs/)

**Example log output:**
```
Using fixture data for restaurants in Capital Region, NY
Using fixture data for events in Capital Region, NY
Generated 4 restaurants, 4 events, 4 pairings
Writing restaurants.json (4 items)
Writing events.json (4 items)
Writing meta.json
Writing config.json
```

## Validating Scheduled Runs

### Check if Scheduled Run Succeeded

#### Method 1: GitHub Actions UI

1. Go to **Actions** tab
2. Look for workflow runs with the clock icon (scheduled)
3. Check status:
   - ✓ Green = successful
   - ✗ Red = failed
   - ○ Yellow = in progress

#### Method 2: Deployment History

1. Go to **Settings** → **Pages**
2. View deployment history
3. Check timestamps - should show daily updates

#### Method 3: Check Site Data

Visit your site and check the footer:

```
Data from Capital Region, NY • Updated: 2025-12-29 at 06:05 UTC
```

The timestamp shows when data was last generated.

#### Method 4: API Endpoint Check

```bash
# Fetch meta.json and check generated_at
curl -s https://username.github.io/repository-name/meta.json | \
  python -c "import sys, json; print(json.load(sys.stdin)['generated_at'])"

# Output: 2025-12-29T06:05:23+00:00
```

### Common Scheduled Run Issues

**Run didn't trigger:**
- GitHub may skip scheduled runs on inactive repos
- Check Actions tab for disabled workflows
- Manual trigger once to reactivate

**Run failed:**
- Check workflow logs for errors
- Often API rate limits or quota exceeded
- Fixture fallback should still work

**Data didn't update:**
- Check `_meta.changed` field in JSON
- If `false`, data hasn't changed since last run
- This is normal - prevents unnecessary updates

**Site not updating:**
- Clear browser cache (Ctrl+Shift+R)
- Check deployment actually completed
- Verify cache headers allow updates

## Troubleshooting

### Deployment Failures

#### Issue: "Failed to build"

**Symptoms:**
```
Error: python -m happenstance.cli aggregate
ModuleNotFoundError: No module named 'requests'
```

**Solution:**
```bash
# Check requirements.txt is present and committed
git add requirements.txt
git commit -m "Add requirements.txt"
git push
```

#### Issue: "API key not found"

**Symptoms:**
```
Warning: GOOGLE_PLACES_API_KEY environment variable not set
Using fixture data for restaurants
```

**Solution:**
1. This is not an error - fixture fallback is working
2. To use real data, add API keys as repository secrets (see Step 3 above)

#### Issue: "Permission denied"

**Symptoms:**
```
Error: Resource not accessible by integration
```

**Solution:**
1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select "Read and write permissions"
3. Save and re-run workflow

#### Issue: "No such file or directory: docs/"

**Symptoms:**
```
Error: Path does not exist: docs
```

**Solution:**
```bash
# Ensure docs/ directory exists
mkdir -p docs
git add docs/.gitkeep
git commit -m "Add docs directory"
git push
```

### Custom Domain Issues

#### Issue: "Domain is not properly configured"

**Symptoms:**
Warning in GitHub Pages settings.

**Solution:**
1. Verify DNS records using `dig yourdomain.com`
2. Wait up to 24 hours for propagation
3. Ensure CNAME record points to `username.github.io` (not `username.github.io/repo`)

#### Issue: "SSL certificate error"

**Symptoms:**
Browser shows "Not Secure" warning.

**Solution:**
1. Wait a few minutes for certificate provisioning
2. Uncheck "Enforce HTTPS", save, then re-check
3. Clear browser cache and retry

### Data Issues

#### Issue: "No events showing"

**Symptoms:**
Events tab empty or shows "No events found"

**Solution:**
```bash
# Check EVENT_WINDOW_DAYS - may be too small
# Add to .github/workflows/pages.yml under env:
EVENT_WINDOW_DAYS: 30

# Or update in config
```

#### Issue: "Pairings not generated"

**Symptoms:**
Paired tab shows "No pairings available"

**Solution:**
1. Check both restaurants and events have data
2. Review geocoding errors in workflow logs
3. Ensure cities in data match region configuration

#### Issue: "Stale data"

**Symptoms:**
Old events still showing after scheduled run

**Solution:**
```bash
# Force manual workflow run
# Go to Actions → Pages Deploy → Run workflow

# Check _meta.changed in JSON
curl https://username.github.io/repo/events.json | \
  python -m json.tool | grep changed
```

## Advanced Configuration

### Customizing Deployment Schedule

Edit `.github/workflows/pages.yml`:

```yaml
on:
  push:
    branches: ["main"]
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * *"  # Change this line
```

**Common schedules:**
- `0 */6 * * *` - Every 6 hours
- `0 6,18 * * *` - 6 AM and 6 PM daily
- `0 6 * * 1,4` - Mondays and Thursdays at 6 AM
- `0 6 1 * *` - First day of each month

### Separate Staging and Production

**Option 1: Branch-based**

Create separate workflows for staging:

```yaml
# .github/workflows/staging.yml
on:
  push:
    branches: ["develop"]
```

Deploy staging to a different Pages site or subdomain.

**Option 2: Environment-based**

Use GitHub Environments:

1. **Settings** → **Environments** → **New environment**
2. Create "production" and "staging"
3. Add different secrets to each
4. Reference in workflow:
   ```yaml
   environment:
     name: production
   ```

### Deployment Notifications

Add notification step to workflow:

```yaml
- name: Notify deployment
  if: success()
  run: |
    curl -X POST https://your-webhook-url \
      -H 'Content-Type: application/json' \
      -d '{"text": "Deployment successful"}'
```

**Services:**
- Slack webhook
- Discord webhook
- Email via SendGrid
- Custom API endpoint

## Performance Optimization

### CDN and Caching

GitHub Pages automatically uses CDN with these cache headers:

```
Cache-Control: max-age=600  # 10 minutes
```

**To verify:**
```bash
curl -I https://username.github.io/repo/restaurants.json
```

### Compression

GitHub Pages automatically enables gzip compression for:
- `.html`
- `.css`
- `.js`
- `.json`

No configuration needed.

### Optimizing Build Time

**Current build time:** ~2-3 minutes

**Optimization strategies:**
1. Limit API result counts (fewer restaurants/events = faster)
2. Reduce geocoding calls (pre-cache coordinates)
3. Skip pairing for very distant events
4. Use fixture data for faster builds during development

## Rollback and Recovery

### Rolling Back to Previous Deployment

**GitHub doesn't support automatic rollback**, but you can:

#### Option 1: Revert Git Commit

```bash
# Find commit hash of working version
git log --oneline

# Revert to that commit
git revert <commit-hash>
git push origin main
```

#### Option 2: Restore from Artifact

1. Download artifact from previous workflow run (if available)
2. Extract to `docs/`
3. Commit and push

#### Option 3: Restore from Backup

Keep backups of `docs/` directory:

```bash
# Before making changes
cp -r docs/ docs-backup-$(date +%Y%m%d)
```

### Disaster Recovery

**If site is completely broken:**

1. Check workflow logs for errors
2. Verify `docs/index.html` exists and is valid
3. Test locally: `python -m happenstance.cli serve`
4. If necessary, restore from git history:
   ```bash
   git checkout <last-known-good-commit> -- docs/
   git commit -m "Restore working docs"
   git push
   ```

## Security Considerations

### API Key Security

**✓ Do:**
- Store API keys as repository secrets
- Use separate keys for staging/production
- Rotate keys periodically
- Monitor API usage dashboards

**✗ Don't:**
- Commit API keys to git
- Share keys in issues or PRs
- Use production keys in forks
- Hardcode keys in workflow files

### Repository Access

**For public repositories:**
- API keys are safe in secrets (not exposed in logs)
- Forkers cannot access your secrets
- Generated data is public (by design)

**For private repositories:**
- Same security model applies
- Pages site can be private (requires GitHub Pro)

### Content Security

The deployed site is static with no backend:
- No server-side code execution
- No database or user data
- No cookies (except GitHub Pages analytics, optional)
- HTML escaping in frontend prevents XSS

## Monitoring and Analytics

### GitHub Analytics

Basic analytics available:
1. **Insights** → **Traffic** (for public repos)
2. Shows page views and unique visitors
3. Limited to 14-day history

### Custom Analytics

Add analytics to `docs/index.html`:

**Google Analytics:**
```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

**Privacy-focused alternatives:**
- Plausible Analytics
- Fathom Analytics
- Simple Analytics

### Uptime Monitoring

Use external monitoring:
- UptimeRobot (free tier available)
- Pingdom
- StatusCake

Monitor endpoints:
- Main page: `https://username.github.io/repo/`
- JSON health check: `https://username.github.io/repo/meta.json`

## Additional Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Custom Domain Help](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)
- [API Setup Guide](API_SETUP.md)
- [Generator Documentation](generator.md)
- [Architecture Overview](ARCHITECTURE.md)
