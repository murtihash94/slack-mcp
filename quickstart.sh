#!/bin/bash

# Quickstart script for deploying Slack MCP Server to Databricks Apps
# This script helps you set up and deploy the server quickly

set -e

echo "=================================="
echo "Slack MCP Server - Databricks Apps"
echo "Quickstart Deployment Script"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo "❌ Databricks CLI is not installed"
    echo "Please install it from: https://docs.databricks.com/dev-tools/cli/install.html"
    exit 1
else
    echo "✅ Databricks CLI is installed"
fi

echo ""
echo "Choose deployment method:"
echo "1) Bundle CLI (Recommended)"
echo "2) Apps CLI"
read -p "Enter choice [1-2]: " choice

# Ask for profile name
read -p "Enter Databricks profile name (default: slack-mcp-server): " profile
profile=${profile:-slack-mcp-server}

# Check if profile exists, if not create it
if ! databricks auth profiles | grep -q "^${profile}$"; then
    echo ""
    echo "Profile '$profile' not found. Let's create it..."
    databricks auth login --profile "$profile"
else
    echo "✅ Using existing profile: $profile"
fi

# Ask for Slack tokens
echo ""
echo "Enter your Slack credentials:"
read -p "SLACK_BOT_TOKEN (starts with xoxb-): " bot_token
read -p "SLACK_USER_TOKEN (starts with xoxp-): " user_token
read -p "Enable safe search mode? (y/n, default: n): " safe_search
safe_search=${safe_search:-n}

if [[ "$safe_search" == "y" ]]; then
    safe_search_value="true"
else
    safe_search_value="false"
fi

# Update app.yaml with tokens
echo ""
echo "Updating app.yaml with your credentials..."
cat > app.yaml << EOF
command: ["uv", "run", "slack-mcp-server"]
env:
  - name: SLACK_BOT_TOKEN
    value: "$bot_token"
  - name: SLACK_USER_TOKEN
    value: "$user_token"
  - name: SLACK_SAFE_SEARCH
    value: "$safe_search_value"
EOF

echo "✅ app.yaml updated"

# Build the wheel
echo ""
echo "Building the wheel package..."
uv build --wheel

if [ $? -eq 0 ]; then
    echo "✅ Wheel built successfully"
else
    echo "❌ Wheel build failed"
    exit 1
fi

# Deploy based on choice
if [ "$choice" == "1" ]; then
    echo ""
    echo "Deploying using Bundle CLI..."
    
    databricks bundle deploy -p "$profile"
    
    if [ $? -eq 0 ]; then
        echo "✅ Bundle deployed successfully"
        echo ""
        echo "Starting the app..."
        databricks bundle run slack-mcp-server -p "$profile"
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "=================================="
            echo "✅ Deployment successful!"
            echo "=================================="
        else
            echo "❌ Failed to start the app"
            exit 1
        fi
    else
        echo "❌ Bundle deployment failed"
        exit 1
    fi
    
elif [ "$choice" == "2" ]; then
    echo ""
    echo "Deploying using Apps CLI..."
    
    # Create app
    echo "Creating app..."
    databricks apps create slack-mcp-server -p "$profile" || echo "App already exists"
    
    # Get username
    username=$(databricks current-user me -p "$profile" | grep -o '"userName":"[^"]*' | cut -d'"' -f4)
    
    if [ -z "$username" ]; then
        echo "❌ Failed to get username"
        exit 1
    fi
    
    echo "Using username: $username"
    
    # Sync files
    echo "Syncing files..."
    databricks sync .build "/Users/$username/slack-mcp-server" -p "$profile"
    
    if [ $? -eq 0 ]; then
        echo "✅ Files synced successfully"
    else
        echo "❌ File sync failed"
        exit 1
    fi
    
    # Deploy app
    echo "Deploying app..."
    databricks apps deploy slack-mcp-server \
        --source-code-path "/Workspace/Users/$username/slack-mcp-server" \
        -p "$profile"
    
    if [ $? -eq 0 ]; then
        echo "✅ App deployed successfully"
    else
        echo "❌ App deployment failed"
        exit 1
    fi
    
    # Start app
    echo "Starting app..."
    databricks apps start slack-mcp-server -p "$profile"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "=================================="
        echo "✅ Deployment successful!"
        echo "=================================="
    else
        echo "❌ Failed to start app"
        exit 1
    fi
else
    echo "Invalid choice"
    exit 1
fi

# Get app URL
echo ""
echo "Getting app information..."
databricks apps list -p "$profile" | grep slack-mcp-server || true

echo ""
echo "Next steps:"
echo "1. Get your app URL from the list above"
echo "2. Get your auth token: databricks auth token -p $profile"
echo "3. Connect to: https://your-app-url/mcp/"
echo "4. Use the token in Authorization: Bearer <token>"
echo ""
echo "For more details, see DEPLOYMENT.md"
