# Deploying Slack MCP Server to Databricks Apps

This guide explains how to deploy the Slack MCP server to Databricks Apps following the Databricks template structure.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Local Development](#local-development)
- [Deployment Methods](#deployment-methods)
  - [Method 1: Using databricks bundle CLI](#method-1-using-databricks-bundle-cli)
  - [Method 2: Using databricks apps CLI](#method-2-using-databricks-apps-cli)
- [Connecting to the Deployed Server](#connecting-to-the-deployed-server)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

1. **uv** - Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
2. **Databricks CLI** - Command-line interface for Databricks ([installation guide](https://docs.databricks.com/dev-tools/cli/index.html))
3. **Databricks Workspace** - Access to a Databricks workspace with Apps capability
4. **Slack App Credentials**:
   - `SLACK_BOT_TOKEN` - Bot User OAuth Token (starts with `xoxb-`)
   - `SLACK_USER_TOKEN` - User OAuth Token (starts with `xoxp-`)

### Setting up Slack Credentials

1. Create a Slack app at https://api.slack.com/apps
2. Configure OAuth scopes for both Bot Token and User Token:
   - Bot Token Scopes: `channels:read`, `chat:write`, `reactions:write`, `users:read`, `conversations.history`
   - User Token Scopes: `search:read` (required for message search)
3. Install the app to your workspace
4. Copy the tokens from OAuth & Permissions page

## Project Structure

The project follows the Databricks MCP server template structure:

```
slack-mcp-server/
├── src/
│   └── slack_server/
│       ├── __init__.py           # Package initialization
│       ├── app.py                # Main FastMCP application with all tools
│       ├── main.py               # Entry point for local development
│       └── static/
│           └── index.html        # Web interface
├── hooks/
│   └── apps_build.py             # Build hook for Databricks Apps
├── pyproject.toml                # Python project configuration
├── databricks.yml                # Databricks bundle configuration
├── app.yaml                      # App runtime configuration
├── README.md                     # Main documentation
└── DEPLOYMENT.md                 # This file
```

## Local Development

To run and test the server locally before deploying:

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Sync dependencies**:
   ```bash
   uv sync
   ```

3. **Set environment variables**:
   ```bash
   export SLACK_BOT_TOKEN="xoxb-your-bot-token"
   export SLACK_USER_TOKEN="xoxp-your-user-token"
   export SLACK_SAFE_SEARCH="false"  # Optional: set to "true" to enable safe search
   ```

4. **Run the server locally**:
   ```bash
   uv run slack-mcp-server
   ```
   
   Or with uvicorn directly:
   ```bash
   uvicorn slack_server.app:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Test the server**:
   - Open http://localhost:8000 in your browser to see the web interface
   - Test the health endpoint: http://localhost:8000/health
   - Connect an MCP client to http://localhost:8000/mcp/

## Deployment Methods

There are two methods to deploy the server to Databricks Apps:

### Method 1: Using databricks bundle CLI

This is the **recommended method** as it provides better integration with Databricks workflows.

#### Step 1: Configure Databricks Authentication

```bash
export DATABRICKS_CONFIG_PROFILE=slack-mcp-server
databricks auth login --profile "$DATABRICKS_CONFIG_PROFILE"
```

Follow the prompts to authenticate with your Databricks workspace.

#### Step 2: Build the Wheel Package

```bash
uv build --wheel
```

This creates a `.whl` file in the `dist/` directory and a `.build/` directory with the Databricks Apps-compatible structure.

#### Step 3: Deploy Using Bundle

```bash
databricks bundle deploy -p slack-mcp-server
```

This command:
- Syncs the `.build` directory to your Databricks workspace
- Creates or updates the app configuration
- Prepares the app for running

#### Step 4: Configure Environment Variables

Before running the app, you need to configure the Slack tokens. Edit the `app.yaml` file in the `.build/` directory or update it directly in Databricks:

```yaml
command: ["uv", "run", "slack-mcp-server"]
env:
  - name: SLACK_BOT_TOKEN
    value: "xoxb-your-actual-bot-token"
  - name: SLACK_USER_TOKEN
    value: "xoxp-your-actual-user-token"
  - name: SLACK_SAFE_SEARCH
    value: "false"
```

#### Step 5: Run the App

```bash
databricks bundle run slack-mcp-server -p slack-mcp-server
```

The app will start and you'll receive the app URL.

### Method 2: Using databricks apps CLI

This method provides more direct control over the deployment.

#### Step 1: Configure Databricks Authentication

```bash
export DATABRICKS_CONFIG_PROFILE=slack-mcp-server
databricks auth login --profile "$DATABRICKS_CONFIG_PROFILE"
```

#### Step 2: Build the Wheel Package

```bash
uv build --wheel
```

#### Step 3: Create the App

```bash
databricks apps create slack-mcp-server -p slack-mcp-server
```

#### Step 4: Upload Source Code

```bash
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync .build "/Users/$DATABRICKS_USERNAME/slack-mcp-server" -p slack-mcp-server
```

#### Step 5: Update app.yaml with Credentials

Make sure your `app.yaml` in the `.build/` directory contains your Slack tokens:

```yaml
command: ["uv", "run", "slack-mcp-server"]
env:
  - name: SLACK_BOT_TOKEN
    value: "xoxb-your-actual-bot-token"
  - name: SLACK_USER_TOKEN
    value: "xoxp-your-actual-user-token"
  - name: SLACK_SAFE_SEARCH
    value: "false"
```

#### Step 6: Deploy the App

```bash
databricks apps deploy slack-mcp-server \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/slack-mcp-server" \
  -p slack-mcp-server
```

#### Step 7: Start the App

```bash
databricks apps start slack-mcp-server -p slack-mcp-server
```

## Connecting to the Deployed Server

After successful deployment, connect to your Slack MCP server using the Streamable HTTP transport.

### Get Your App URL

```bash
databricks apps list -p slack-mcp-server
```

The URL typically follows this format:
```
https://<workspace-id>.cloud.databricks.com/apps/<app-id>
```

### MCP Endpoint

The MCP endpoint is available at:
```
https://your-app-url.databricksapps.com/mcp/
```

**Important**: The URL must end with `/mcp/` (including the trailing slash).

### Authentication

Get your Databricks authentication token:

```bash
databricks auth token -p slack-mcp-server
```

Use this token in the `Authorization` header:
```
Authorization: Bearer <your-token>
```

### Example: Claude Desktop Configuration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "slack-databricks": {
      "url": "https://your-app-url.databricksapps.com/mcp/",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer YOUR_DATABRICKS_TOKEN"
      }
    }
  }
}
```

### Example: MCP Inspector

```bash
npx @modelcontextprotocol/inspector \
  --transport http \
  --url https://your-app-url.databricksapps.com/mcp/ \
  --header "Authorization: Bearer YOUR_DATABRICKS_TOKEN"
```

## Configuration

### Environment Variables

The server supports the following environment variables:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `SLACK_BOT_TOKEN` | Yes | Slack Bot User OAuth Token | - |
| `SLACK_USER_TOKEN` | Yes | Slack User OAuth Token | - |
| `SLACK_SAFE_SEARCH` | No | Filter private channels/DMs from search | `false` |

### Safe Search Mode

When `SLACK_SAFE_SEARCH=true`, the server automatically filters out:
- Private channels
- Direct messages (DMs)
- Multi-party direct messages (MPDMs)

This provides an additional security layer for enterprise deployments.

## Troubleshooting

### Common Issues

#### 1. Build Fails

**Problem**: `uv build --wheel` fails

**Solution**:
```bash
# Ensure uv is up to date
uv self update

# Clean and rebuild
rm -rf dist/ .build/
uv build --wheel
```

#### 2. App Won't Start

**Problem**: App status shows as failed

**Solution**:
- Check app logs:
  ```bash
  databricks apps logs slack-mcp-server -p slack-mcp-server
  ```
- Verify environment variables are set correctly in `app.yaml`
- Ensure Slack tokens are valid and have correct scopes

#### 3. Authentication Errors

**Problem**: MCP client can't connect due to auth errors

**Solution**:
- Refresh your Databricks token:
  ```bash
  databricks auth token -p slack-mcp-server --refresh
  ```
- Ensure app service principal has necessary permissions

#### 4. Slack API Errors

**Problem**: Tools return "Slack API error"

**Solution**:
- Verify Slack tokens are correct and not expired
- Check that your Slack app has the required OAuth scopes
- Ensure the bot is invited to channels you're trying to access

### Getting Help

For issues specific to:
- **Slack MCP Server**: Check the main [README.md](README.md)
- **Databricks Apps**: Refer to [Databricks Apps documentation](https://docs.databricks.com/apps/)
- **MCP Protocol**: Visit [Model Context Protocol documentation](https://modelcontextprotocol.io/)

### Debugging

Enable debug logging by setting in `app.yaml`:

```yaml
command: ["uv", "run", "slack-mcp-server"]
env:
  - name: SLACK_BOT_TOKEN
    value: "xoxb-..."
  - name: SLACK_USER_TOKEN
    value: "xoxp-..."
  - name: LOG_LEVEL
    value: "DEBUG"
```

View logs in real-time:

```bash
databricks apps logs slack-mcp-server -p slack-mcp-server --follow
```

## Updating the Deployment

To update an existing deployment with new changes:

### Using bundle CLI:

```bash
# Rebuild
uv build --wheel

# Redeploy
databricks bundle deploy -p slack-mcp-server

# Restart
databricks bundle run slack-mcp-server -p slack-mcp-server
```

### Using apps CLI:

```bash
# Rebuild
uv build --wheel

# Sync changes
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync .build "/Users/$DATABRICKS_USERNAME/slack-mcp-server" -p slack-mcp-server

# Redeploy
databricks apps deploy slack-mcp-server \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/slack-mcp-server" \
  -p slack-mcp-server

# Restart
databricks apps restart slack-mcp-server -p slack-mcp-server
```

## Security Considerations

1. **Never commit tokens**: Keep `SLACK_BOT_TOKEN` and `SLACK_USER_TOKEN` out of version control
2. **Use safe search**: Enable `SLACK_SAFE_SEARCH=true` in production to prevent access to private conversations
3. **Token rotation**: Regularly rotate Slack tokens
4. **Databricks permissions**: Ensure only authorized users can access the app
5. **Network security**: Use Databricks network policies if required

## Additional Resources

- [Slack API Documentation](https://api.slack.com/docs)
- [Databricks Apps Guide](https://docs.databricks.com/apps/)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Template Repository](https://github.com/murtihash94/custom_mcp_server_databricks)
