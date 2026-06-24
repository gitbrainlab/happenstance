# GitHub Pages Deployment Setup

## Issue

The GitHub Pages deployment workflow is failing at the deploy step. This is typically due to GitHub Pages not being properly configured for the repository.

## Solution

### Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click on "Settings" tab
3. Scroll down to "Pages" section (in the left sidebar under "Code and automation")
4. Under "Build and deployment":
   - **Source**: Select "GitHub Actions" (not "Deploy from a branch")
   - This allows the workflow to deploy directly

### Step 2: Verify Workflow Permissions

1. In repository Settings → Actions → General
2. Scroll to "Workflow permissions"
3. Ensure either:
   - "Read and write permissions" is selected, OR
   - "Read repository contents and packages permissions" with "Allow GitHub Actions to create and approve pull requests" checked

### Step 3: Verify Environment

The workflow uses the `github-pages` environment. Ensure it's configured:

1. Go to Settings → Environments
2. You should see a `github-pages` environment
3. If not present, it will be created automatically on first successful run
4. No special protection rules are needed for public repositories

### Step 4: Run the Workflow

After configuration:

1. Go to Actions tab
2. Select "Pages Deploy" workflow
3. Click "Run workflow" → "Run workflow"
4. Monitor the build and deploy jobs

### Step 5: Verify Deployment

Once successful:
- The site will be available at: `https://[username].github.io/happenstance/`
- Build artifacts will be created and deployed automatically
- Daily updates will run at 6 AM UTC via the scheduled cron job

## Common Issues

### "Deployment failed" error
- **Cause**: Pages not configured to use GitHub Actions
- **Fix**: Set Source to "GitHub Actions" in Pages settings

### "Permission denied" error
- **Cause**: Insufficient workflow permissions
- **Fix**: Enable read/write permissions in Actions settings

### "Environment not found" error
- **Cause**: github-pages environment doesn't exist
- **Fix**: It will be created on first workflow run; may need to rerun workflow

### Build succeeds but deploy fails
- **Cause**: Pages may not be enabled
- **Fix**: Enable Pages in Settings → Pages

## Current Status

The workflow has been updated to:
- ✅ Fetch data using API keys from repository secrets
- ✅ Fall back to fixture data if API keys are missing
- ✅ Generate fresh JSON data files
- ✅ Upload Pages artifact
- ❌ Deploy to GitHub Pages (requires repository configuration)

After configuring Pages, the workflow will:
1. Run daily at 6 AM UTC
2. Fetch fresh restaurant and event data from APIs (if keys provided)
3. Generate updated JSON files
4. Deploy to GitHub Pages automatically

## Testing

To test the workflow manually:
1. Go to Actions → Pages Deploy
2. Click "Run workflow"
3. Select branch (default: main)
4. Click "Run workflow"
5. Watch the build and deploy jobs

## API Keys

Don't forget to add API keys as repository secrets for real data:
- `GOOGLE_PLACES_API_KEY`
- `GOOGLE_CSE_ID` (optional, enables Google-backed event search)
- `TICKETMASTER_API_KEY`
- `EVENTBRITE_API_KEY`

See [API_SETUP.md](API_SETUP.md) for details.

## Next Steps

After fixing the Pages deployment:
1. Verify the site loads at your GitHub Pages URL
2. Add API keys as repository secrets
3. Run the workflow again to fetch real data
4. Check that restaurant and event data is updated
