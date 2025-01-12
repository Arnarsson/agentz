#!/bin/bash

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is not installed. Please install it first:"
    echo "brew install gh"
    exit 1
fi

# Check if logged in to GitHub CLI
if ! gh auth status &> /dev/null; then
    echo "Please login to GitHub CLI first:"
    echo "gh auth login"
    exit 1
fi

# Check for required environment variables
if [ -z "$OPENAI_API_KEY" ] || [ -z "$CLERK_SECRET_KEY" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "Error: Missing required environment variables"
    echo "Please set the following environment variables:"
    echo "- OPENAI_API_KEY"
    echo "- CLERK_SECRET_KEY"
    echo "- SUPABASE_KEY"
    exit 1
fi

# Get the repository name from git remote
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
if [ -z "$REPO" ]; then
    echo "Error: Could not determine repository name"
    exit 1
fi

# Set secrets using environment variables
echo "Setting up GitHub repository secrets..."

# OpenAI API Key
gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY"
echo "✓ Set OPENAI_API_KEY"

# Clerk Secret Key
gh secret set CLERK_SECRET_KEY --body "$CLERK_SECRET_KEY"
echo "✓ Set CLERK_SECRET_KEY"

# Supabase Key
gh secret set SUPABASE_KEY --body "$SUPABASE_KEY"
echo "✓ Set SUPABASE_KEY"

echo "All secrets have been set successfully!" 