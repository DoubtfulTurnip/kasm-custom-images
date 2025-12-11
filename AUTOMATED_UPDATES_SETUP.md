# Automated Updates Setup Guide

## Overview
The `check-versions.yml` workflow automatically detects new versions of upstream applications and updates Dockerfiles. To enable automatic commits and pushes, you need to configure a Personal Access Token (PAT).

## Why is a PAT Required?
The default `GITHUB_TOKEN` provided by GitHub Actions cannot trigger other workflows (like build workflows) to prevent recursive workflow runs. A PAT with appropriate permissions allows the automated update workflow to:
1. Push commits to the repository
2. Trigger downstream build workflows automatically

## Setup Instructions

### Step 1: Create a Personal Access Token (PAT)

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Direct link: https://github.com/settings/tokens

2. Click "Generate new token" → "Generate new token (classic)"

3. Configure the token:
   - **Note**: `kasm-custom-images automated updates`
   - **Expiration**: Choose your preferred expiration (90 days, 1 year, or no expiration)
   - **Scopes**: Select the following permissions:
     - ✅ `repo` (Full control of private repositories)
       - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
     - ✅ `workflow` (Update GitHub Action workflows)

4. Click "Generate token" at the bottom

5. **IMPORTANT**: Copy the token immediately - you won't be able to see it again!

### Step 2: Add PAT as Repository Secret

1. Go to your repository: https://github.com/DoubtfulTurnip/kasm-custom-images

2. Navigate to Settings → Secrets and variables → Actions

3. Click "New repository secret"

4. Configure the secret:
   - **Name**: `PAT` (exactly this name - it's referenced in the workflow)
   - **Secret**: Paste the token you copied in Step 1

5. Click "Add secret"

### Step 3: Verify Setup

1. Go to Actions tab in your repository

2. Find the "Check Upstream Versions" workflow

3. Click "Run workflow" to manually trigger it

4. The workflow should now:
   - ✅ Check for version updates
   - ✅ Update Dockerfiles if needed
   - ✅ Commit changes automatically
   - ✅ Push to repository
   - ✅ Trigger build workflows for updated containers

## How It Works

### Automated Flow
```
Weekly Schedule (Monday 00:00 UTC)
  ↓
Check Upstream Versions Workflow Runs
  ↓
Query GitHub API for Latest Releases
  ↓
Compare with Current Versions in Dockerfiles
  ↓
If Updates Available:
  - Update Dockerfiles using sed
  - Commit changes
  - Push to repository
  ↓
Build Workflows Automatically Trigger
  ↓
New Containers Built and Pushed to Docker Hub
```

### Applications Monitored
- **Trufflehog** - Detects GitHub releases
- **Webcheck** - Detects GitHub releases
- **Hayabusa** (Takajo) - Detects GitHub releases
- **Chainsaw** (Takajo) - Detects GitHub releases
- **Epagneul** - Detects GitHub releases
- **Slasher** - Monitors main branch commits
- **SocialAnalyzer** - Uses main branch (manual updates only)

## Troubleshooting

### Workflow Fails with "Permission denied"
- Ensure the PAT secret is named exactly `PAT`
- Verify the PAT has `repo` and `workflow` scopes
- Check that the PAT hasn't expired

### Build Workflows Don't Trigger After Update
- Verify the PAT has `workflow` scope enabled
- Check that the PAT belongs to a user with write access to the repository

### No Updates Detected
- The workflow runs weekly - updates may not be available every week
- Check the workflow summary to see current vs latest versions
- Manually trigger the workflow to force a check

## Manual Workflow Trigger

You can manually trigger the version check workflow:

1. Go to Actions → Check Upstream Versions
2. Click "Run workflow"
3. Select branch: `main`
4. Click "Run workflow"

This is useful for:
- Testing after initial setup
- Forcing an immediate check for updates
- Debugging issues

## Token Security Best Practices

1. **Use minimal permissions**: Only grant `repo` and `workflow` scopes
2. **Set expiration**: Use 90-day or 1-year expiration for security
3. **Rotate regularly**: Before expiration, generate a new token and update the secret
4. **Monitor usage**: Check Actions logs to ensure the token is working correctly
5. **Revoke if compromised**: Immediately revoke and regenerate if the token is exposed

## Notification Setup (Optional)

To get notified when workflows fail:

1. Go to repository Settings → Notifications
2. Enable "Actions" notifications
3. Choose notification method (email, mobile, etc.)

You'll be notified if:
- The check-versions workflow fails
- Build workflows fail after automated updates

## Current Status

After completing the setup above, your repository will have:
- ✅ Automated version monitoring (weekly)
- ✅ Automatic Dockerfile updates
- ✅ Automatic commits and pushes
- ✅ Automatic Docker builds
- ✅ Automatic Docker Hub pushes

**Result**: Fully automated container updates with zero manual intervention!
