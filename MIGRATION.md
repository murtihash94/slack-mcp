# Migration Guide: TypeScript to Python (Databricks Apps)

This document explains the changes made to convert the Slack MCP server from TypeScript to Python for Databricks Apps deployment.

## Overview

The server has been converted to support Databricks Apps deployment while maintaining **100% feature parity** with the original TypeScript implementation. Both versions can coexist in the repository.

## What Changed

### Language & Framework

| Component | TypeScript (Original) | Python (Databricks) |
|-----------|----------------------|---------------------|
| Language | TypeScript/Node.js | Python 3.11+ |
| MCP Framework | @modelcontextprotocol/sdk | mcp[cli] (FastMCP) |
| HTTP Server | Express | FastAPI |
| Runtime | Node.js | uvicorn |
| Package Manager | npm | uv |
| Build System | TypeScript Compiler | hatchling |

### File Structure

#### TypeScript Version
```
src/
├── index.ts          # Main server code
└── schemas.ts        # Zod schemas
package.json          # Dependencies
tsconfig.json         # TypeScript config
```

#### Python Version (NEW)
```
src/
└── slack_server/
    ├── __init__.py         # Package init
    ├── app.py              # Main FastMCP app
    ├── main.py             # Entry point
    └── static/
        └── index.html      # Web interface
hooks/
└── apps_build.py           # Build hook
pyproject.toml              # Project config
databricks.yml              # Bundle config
app.yaml                    # App config
requirements.txt            # Dependencies
DEPLOYMENT.md               # Deployment guide
quickstart.sh               # Quick deploy script
```

## Feature Comparison

All features are preserved in both versions:

| Feature | TypeScript | Python | Notes |
|---------|-----------|--------|-------|
| slack_list_channels | ✅ | ✅ | Identical functionality |
| slack_post_message | ✅ | ✅ | Identical functionality |
| slack_reply_to_thread | ✅ | ✅ | Identical functionality |
| slack_add_reaction | ✅ | ✅ | Identical functionality |
| slack_get_channel_history | ✅ | ✅ | Identical functionality |
| slack_get_thread_replies | ✅ | ✅ | Identical functionality |
| slack_get_users | ✅ | ✅ | Identical functionality |
| slack_get_user_profiles | ✅ | ✅ | Identical functionality |
| slack_search_messages | ✅ | ✅ | Identical functionality |
| slack_search_channels | ✅ | ✅ | Identical functionality |
| slack_search_users | ✅ | ✅ | Identical functionality |
| Safe Search Mode | ✅ | ✅ | Identical functionality |
| Pagination | ✅ | ✅ | Identical functionality |
| Error Handling | ✅ | ✅ | Adapted to Python |

## Code Comparison Examples

### Tool Definition

**TypeScript:**
```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  switch (request.params.name) {
    case 'slack_list_channels': {
      const args = ListChannelsRequestSchema.parse(request.params.arguments);
      const response = await slackClient.conversations.list({
        limit: args.limit,
        cursor: args.cursor,
        types: 'public_channel',
      });
      return {
        content: [{ type: 'text', text: JSON.stringify(parsed) }],
      };
    }
  }
});
```

**Python:**
```python
@mcp.tool()
def slack_list_channels(
    limit: int = 100,
    cursor: Optional[str] = None
) -> Dict[str, Any]:
    """List public channels in the workspace with pagination."""
    response = slack_client.conversations_list(
        limit=limit,
        cursor=cursor,
        types="public_channel"
    )
    return {
        "channels": [...],
        "response_metadata": response.get("response_metadata", {})
    }
```

### Environment Variables

**TypeScript:**
```typescript
import dotenv from 'dotenv';
dotenv.config();

if (!process.env.SLACK_BOT_TOKEN) {
  console.error('SLACK_BOT_TOKEN is not set');
  process.exit(1);
}

const slackClient = new WebClient(process.env.SLACK_BOT_TOKEN);
```

**Python:**
```python
import os

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")

slack_client = WebClient(token=SLACK_BOT_TOKEN)
```

### HTTP Server Setup

**TypeScript:**
```typescript
const app = express();
app.use(express.json());

app.post('/mcp', async (req, res) => {
  const transport = new StreamableHTTPServerTransport({...});
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}/mcp`);
});
```

**Python:**
```python
mcp = FastMCP("Slack MCP Server on Databricks Apps")
mcp_app = mcp.streamable_http_app()

app = FastAPI(
    lifespan=lambda _: mcp.session_manager.run(),
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.mount("/", mcp_app)
```

## Deployment Comparison

### TypeScript (NPM)

**Installation:**
```bash
npm install @ubie-oss/slack-mcp-server
```

**Running:**
```bash
# Stdio
npx @ubie-oss/slack-mcp-server

# HTTP
npx @ubie-oss/slack-mcp-server -port 3000
```

**Configuration (Claude Desktop):**
```json
{
  "slack": {
    "command": "npx",
    "args": ["-y", "@ubie-oss/slack-mcp-server"],
    "env": {
      "SLACK_BOT_TOKEN": "...",
      "SLACK_USER_TOKEN": "..."
    }
  }
}
```

### Python (Databricks Apps)

**Installation:**
```bash
uv build --wheel
```

**Deployment:**
```bash
# Quick deployment
./quickstart.sh

# Or manual
databricks bundle deploy -p <profile>
databricks bundle run slack-mcp-server -p <profile>
```

**Configuration (MCP Client):**
```json
{
  "slack-databricks": {
    "url": "https://your-app-url/mcp/",
    "transport": "http",
    "headers": {
      "Authorization": "Bearer YOUR_DATABRICKS_TOKEN"
    }
  }
}
```

## Migration Benefits

### Python/Databricks Version Benefits

1. **Enterprise Deployment**: Production-ready deployment on Databricks Apps
2. **Managed Infrastructure**: Databricks handles scaling, monitoring, and availability
3. **Integrated Authentication**: Uses Databricks authentication/authorization
4. **Cost Efficiency**: Pay-per-use model on Databricks
5. **Observability**: Built-in logging and monitoring through Databricks
6. **Security**: Enterprise-grade security and compliance

### When to Use Each Version

**Use TypeScript/NPM version when:**
- Running locally for development
- Integrating with Claude Desktop
- Using in a Node.js environment
- Need stdio transport
- Quick prototyping

**Use Python/Databricks version when:**
- Deploying to production
- Need enterprise-grade reliability
- Want managed infrastructure
- Require integration with Databricks ecosystem
- Need centralized authentication

## Compatibility Notes

Both versions:
- Use the same MCP protocol
- Expose the same tools with identical parameters
- Return the same response formats
- Support the same Slack API features
- Can be used interchangeably by MCP clients

## Testing Both Versions

You can test both versions in the same repository:

**TypeScript:**
```bash
npm install
npm run build
npm start
```

**Python:**
```bash
export SLACK_BOT_TOKEN="..."
export SLACK_USER_TOKEN="..."
uv run slack-mcp-server
```

## Troubleshooting Common Issues

### Import Errors (Python)

**Problem:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:**
```bash
uv sync
# or
pip install -r requirements.txt
```

### Build Errors (Python)

**Problem:** `uv build --wheel` fails

**Solution:**
```bash
uv self update
rm -rf dist/ .build/
uv build --wheel
```

### Slack SDK Differences

The Python `slack_sdk` library has slightly different method names:

| TypeScript | Python |
|-----------|--------|
| `conversations.list()` | `conversations_list()` |
| `chat.postMessage()` | `chat_postMessage()` |
| `users.list()` | `users_list()` |
| `search.messages()` | `search_messages()` |

Both use the same underlying Slack API endpoints.

## Future Considerations

The repository now supports both implementations:

1. **TypeScript version** remains the default for NPM users
2. **Python version** is the recommended path for Databricks Apps deployment
3. Both versions will be maintained in parallel
4. New features should be added to both versions

## Additional Resources

- [TypeScript MCP SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [FastMCP (Python)](https://github.com/jlowin/fastmcp)
- [Databricks Apps Documentation](https://docs.databricks.com/apps/)
- [Slack SDK for Python](https://github.com/slackapi/python-slack-sdk)
- [Deployment Guide](DEPLOYMENT.md)
